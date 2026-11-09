"""Video generation through fal.ai's queued model API."""

import asyncio
import logging
import re
import time
import uuid
from pathlib import Path
from urllib.parse import urlparse

import httpx

from config import settings

logger = logging.getLogger(__name__)

FAL_QUEUE_URL = "https://queue.fal.run"
MAX_VIDEO_SIZE = 200 * 1024 * 1024
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


class FalVideoError(Exception):
    def __init__(self, detail: str, status_code: int = 502):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


def _validate_model_id() -> str:
    model_id = settings.FAL_VIDEO_MODEL.strip("/")
    if not model_id or any(part in {"", ".", ".."} for part in model_id.split("/")):
        raise FalVideoError("FAL_VIDEO_MODEL must be a valid fal.ai model ID.", 500)
    return model_id


def _check_response(response: httpx.Response, operation: str) -> None:
    if response.is_success:
        return

    status_code = response.status_code
    logger.warning("fal.ai %s failed with HTTP %s", operation, status_code)
    if status_code in (401, 403):
        raise FalVideoError(
            "fal.ai rejected the configured key. Set a valid FAL_KEY in backend/.env and restart the backend.",
            502,
        )
    if status_code == 402:
        raise FalVideoError("fal.ai requires an active account or sufficient balance.", 402)
    if status_code == 429:
        raise FalVideoError("fal.ai rate-limited this request. Wait and try again.", 429)
    raise FalVideoError(f"fal.ai {operation} failed with HTTP {status_code}.")


def _read_json_object(response: httpx.Response, operation: str) -> dict:
    try:
        payload = response.json()
    except ValueError as exc:
        raise FalVideoError(f"fal.ai returned invalid JSON while {operation}.") from exc
    if not isinstance(payload, dict):
        raise FalVideoError(f"fal.ai returned an invalid response while {operation}.")
    return payload


async def generate_fal_video(
    prompt: str,
    is_short: bool,
    duration: str,
    generate_audio: bool,
) -> tuple[Path, int]:
    """Submit a video request, poll fal.ai, and save the resulting MP4 locally."""
    if not settings.FAL_VIDEO_ENABLED:
        raise FalVideoError(
            "fal.ai video generation is disabled. Set FAL_VIDEO_ENABLED=true after rotating and configuring FAL_KEY.",
            503,
        )
    if not settings.FAL_KEY:
        raise FalVideoError(
            "fal.ai is not configured. Set FAL_KEY in backend/.env and restart the backend.",
            503,
        )

    model_id = _validate_model_id()
    timeout_seconds = max(settings.FAL_VIDEO_TIMEOUT_SECONDS, 1)
    headers = {"Authorization": f"Key {settings.FAL_KEY}"}
    request_payload = {
        "prompt": prompt,
        "aspect_ratio": "9:16" if is_short else "16:9",
        "duration": duration,
        "resolution": "720p",
        "generate_audio": generate_audio,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        submit_response = await client.post(
            f"{FAL_QUEUE_URL}/{model_id}",
            headers=headers,
            json=request_payload,
        )
        _check_response(submit_response, "request submission")
        submit_data = _read_json_object(submit_response, "submitting a request")
        request_id = submit_data.get("request_id")
        if not isinstance(request_id, str) or not REQUEST_ID_PATTERN.fullmatch(request_id):
            raise FalVideoError("fal.ai did not return a valid video request ID.")

        status_url = f"{FAL_QUEUE_URL}/{model_id}/requests/{request_id}/status"
        result_url = f"{FAL_QUEUE_URL}/{model_id}/requests/{request_id}"
        deadline = time.monotonic() + timeout_seconds

        while True:
            if time.monotonic() >= deadline:
                raise FalVideoError(
                    "fal.ai video generation timed out. Check the fal.ai request status before retrying."
                )

            status_response = await client.get(status_url, headers=headers)
            _check_response(status_response, "status check")
            status_data = _read_json_object(status_response, "checking request status")
            status = status_data.get("status")

            if status == "COMPLETED":
                break
            if status not in {"IN_QUEUE", "IN_PROGRESS"}:
                raise FalVideoError("fal.ai returned an unexpected video request status.")
            await asyncio.sleep(min(2, max(deadline - time.monotonic(), 0)))

        result_response = await client.get(result_url, headers=headers)
        _check_response(result_response, "result retrieval")
        result_data = _read_json_object(result_response, "retrieving the generated video")
        video = result_data.get("video")
        video_url = video.get("url") if isinstance(video, dict) else None
        if not isinstance(video_url, str):
            raise FalVideoError("fal.ai returned an invalid video file URL.")
        parsed_url = urlparse(video_url)
        if (
            parsed_url.scheme != "https"
            or not parsed_url.hostname
            or not (parsed_url.hostname == "fal.media" or parsed_url.hostname.endswith(".fal.media"))
        ):
            raise FalVideoError("fal.ai returned an invalid video file URL.")

        filename = f"fal_video_{uuid.uuid4().hex}.mp4"
        output_path = settings.VIDEOS_DIR / filename
        downloaded_size = 0
        download_complete = False
        try:
            async with client.stream("GET", video_url, follow_redirects=True) as download:
                _check_response(download, "video download")
                final_host = download.url.host
                if final_host != "fal.media" and not final_host.endswith(".fal.media"):
                    raise FalVideoError("fal.ai redirected the video download to an untrusted host.")
                content_type = download.headers.get("content-type", "").split(";", 1)[0].lower()
                if content_type and content_type not in {"video/mp4", "application/octet-stream"}:
                    raise FalVideoError("fal.ai returned a file that is not an MP4 video.")

                with output_path.open("wb") as output_file:
                    async for chunk in download.aiter_bytes():
                        downloaded_size += len(chunk)
                        if downloaded_size > MAX_VIDEO_SIZE:
                            raise FalVideoError("Generated video exceeds the 200 MiB download limit.", 413)
                        output_file.write(chunk)
            if downloaded_size == 0:
                raise FalVideoError("fal.ai returned an empty video file.")
            download_complete = True
        finally:
            if not download_complete:
                output_path.unlink(missing_ok=True)

    return output_path, int(duration[:-1])
