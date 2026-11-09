# YouTube AI Command Center

**AI-powered YouTube content automation platform**

Generate scripts with local Ollama, create AI voiceovers (Edge TTS), assemble videos (MoviePy + Pexels), design thumbnails, schedule content, and upload to YouTube via official API — all from a modern dark glass dashboard.

---

## Architecture

```
youtube-ai-automation/
├── backend/                 # FastAPI + SQLAlchemy + services
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── routers/             # API endpoints
│   ├── services/            # Ollama, TTS, Video, YouTube, etc.
│   ├── utils/
│   ├── generated/           # scripts, audio, videos, thumbnails
│   ├── requirements.txt
│   └── .env.example
├── frontend/                # React + Vite + Tailwind
│   ├── src/
│   │   ├── components/
│   │   ├── pages/           # All dashboard sections
│   │   ├── layouts/
│   │   ├── services/api.js
│   │   ├── context/
│   │   └── ...
│   ├── package.json
│   └── vite.config.js
└── README.md
```

---

## Prerequisites (Windows 11)

1. **Python 3.12+** – https://www.python.org/downloads/ (check “Add to PATH”)
2. **Node.js 18+** – https://nodejs.org/
3. **Ollama** – https://ollama.com/download
4. **FFmpeg** (required by MoviePy)
   - Download: https://www.gyan.dev/ffmpeg/builds/
   - Extract and add `bin` folder to system PATH
   - Verify: `ffmpeg -version`
5. **Git** (optional)

---

## 1. Ollama Setup

```bash
# After installing Ollama, open a terminal:
ollama serve

# In another terminal, pull a model (choose one):
ollama pull llama3.2
# or: ollama pull mistral
# or: ollama pull phi3
```

Confirm: open http://localhost:11434 in browser or run `ollama list`.

---

## 2. Backend Setup

```bash
cd youtube-ai-automation/backend

# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1
# Or CMD: venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt

# Environment
copy .env.example .env
# Edit .env with Notepad and fill keys (see below)
```

### Backend `.env` keys

| Key | Required | Description |
|-----|----------|-------------|
| `SECRET_KEY` | Yes | Long random string |
| `OLLAMA_BASE_URL` | Yes | Default `http://localhost:11434` |
| `OLLAMA_MODEL` | Yes | e.g. `llama3.2` |
| `PEXELS_API_KEY` | Recommended | Free at https://www.pexels.com/api/ |
| `FAL_KEY` | Optional | Backend-only fal.ai key used for AI video generation |
| `FAL_VIDEO_ENABLED` | Optional | Set `true` after rotating/configuring the key to enable paid video generation |
| `FAL_VIDEO_MODEL` | Optional | Default `fal-ai/veo3.1/fast` |
| `FAL_VIDEO_TIMEOUT_SECONDS` | Optional | Queue timeout; default `600` |
| `GOOGLE_CLIENT_ID` | For YouTube upload | Google Cloud OAuth |
| `GOOGLE_CLIENT_SECRET` | For YouTube upload | Google Cloud OAuth |
| `GOOGLE_REDIRECT_URI` | For YouTube | `http://localhost:8000/api/v1/youtube/oauth/callback` |
| `GOOGLE_LOGIN_REDIRECT_URI` | For Google sign-in | `http://localhost:8000/api/v1/auth/google/callback` |
| `GITHUB_CLIENT_ID` | For GitHub sign-in | GitHub OAuth App client ID |
| `GITHUB_CLIENT_SECRET` | For GitHub sign-in | GitHub OAuth App client secret |
| `GITHUB_REDIRECT_URI` | For GitHub sign-in | `http://localhost:8000/api/v1/auth/github/callback` |

For Google sign-in, add the login callback URI to the same Google OAuth client's
authorized redirect URIs. For GitHub, create an OAuth App with the backend
callback URL as its Authorization callback URL. Set the production callback
URLs to your Render service's HTTPS origin and configure the client ID/secret
in Render. Both providers require a verified email address.

### Run backend

```bash
# From backend/ with venv active
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- API docs: http://localhost:8000/docs  
- Health: http://localhost:8000/health  

---

## 3. Frontend Setup

```bash
cd youtube-ai-automation/frontend

npm install
npm run dev
```

Open: **http://localhost:5173**

The Vite proxy forwards `/api` and `/media` to the backend.

---

## 4. Google OAuth / YouTube API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or select one)
3. **APIs & Services → Library** → enable **YouTube Data API v3**
4. **APIs & Services → Credentials → Create Credentials → OAuth client ID**
   - Application type: **Web application**
   - Authorized redirect URIs:  
     `http://localhost:8000/api/v1/youtube/oauth/callback`
5. Copy Client ID and Client Secret into `backend/.env`
6. **OAuth consent screen**: add your Google account as a test user (while app is in Testing mode)
7. In the dashboard go to **YouTube Channel → Connect with Google**

**Important:** Public uploads require the `approve=true` flag in the API (and the UI checkbox). Default is private.

---

## 5. First-Time Workflow

No account is required to use the local dashboard. Open http://localhost:5173 to get started.

1. **API Settings** – confirm Ollama is available
2. **Script Studio** – enter a topic and generate a script
3. **Voice Studio** – select a script and create a voiceover
4. **Video Generator** – select a script to compose a video, or generate a prompt-based Veo clip with fal.ai
5. **Thumbnail Generator** – optionally create a custom thumbnail
6. **YouTube Channel** – connect Google OAuth when you’re ready to publish
7. **Upload Manager** – choose a video and visibility; public uploads require approval

---

## 6. Local Testing Checklist

| Feature | How to test |
|---------|-------------|
| Access | Open the dashboard without signing in |
| Script | Generate with Ollama running |
| Voice | Generate MP3 and play in browser |
| Video | Create short; check `backend/generated/videos` |
| Thumbnail | Generate and preview |
| Research | Content Calendar page |
| YouTube | Connect + private upload |
| Scheduler | Create cron schedule (execution is recorded; full worker can be extended with APScheduler) |

---

## 7. Troubleshooting

| Problem | Fix |
|---------|-----|
| `Ollama connection refused` | Run `ollama serve` and `ollama pull llama3.2` |
| MoviePy / video fails | Install FFmpeg and ensure it is on PATH |
| `No module named 'moviepy'` or `'moviepy.editor'` | From `backend/`, run `pip install -r requirements.txt` and restart the backend. This project uses MoviePy 2. |
| CORS errors | Backend CORS allows `http://localhost:5173` |
| YouTube 403 | OAuth consent screen + test user; correct redirect URI |
| Pexels empty | Set `PEXELS_API_KEY`; system falls back to solid background |
| fal.ai video unavailable | Set a rotated `FAL_KEY` and `FAL_VIDEO_ENABLED=true` in backend `.env`, check your fal.ai account balance, then restart the backend |
| bcrypt / passlib errors | `pip install bcrypt==4.2.1` |
| ImageMagick / TextClip | Title overlay may skip if fonts missing; video still renders |

---

## 8. Deployment Notes (production)

- Change `SECRET_KEY` and set `DEBUG=False`
- Use PostgreSQL instead of SQLite (`DATABASE_URL`)
- Run uvicorn behind Nginx / Caddy with HTTPS
- Store OAuth tokens encrypted
- Use a real job queue (Celery + Redis) for long video renders and schedules
- Never expose `.env` or generated media without auth in production

### Render backend (Step 2)

The root `render.yaml` configures the Python service. Push the repository to GitHub,
then in Render choose **New → Blueprint**, select that repository, and apply the
blueprint. Set the prompted `DEFAULT_PASSWORD` to a unique password of at least
12 characters. Render generates `SECRET_KEY`; do not replace it with a committed
value. The backend refuses to start in production if guest access is enabled, the
secret key is unchanged/too short, or the default admin password is still in use.

After deployment, the API URL is the Render service URL (for example,
`https://your-service.onrender.com`); check `/health` and `/docs`. The initial
administrator username is `admin`, and its password is the `DEFAULT_PASSWORD`
you entered in Render. Public registration is disabled in production.

For the Netlify frontend, set `VITE_AUTH_REQUIRED=true` and
`VITE_API_BASE_URL=https://your-service.onrender.com/api/v1` in the Netlify
build environment. In Render, set `FRONTEND_URL` to the deployed Netlify origin.
If using YouTube OAuth, set `GOOGLE_REDIRECT_URI` to
`https://your-service.onrender.com/api/v1/youtube/oauth/callback` and register
that exact URI in Google Cloud.

The free service can sleep while idle. Ollama is not included on Render; configure
a reachable hosted LLM endpoint before using features that require Ollama.

### Supabase PostgreSQL (Step 3)

1. Create a Supabase project and save its database password securely.
2. In the Supabase dashboard, open **Connect** and choose the **Session pooler**
   connection string (not the direct database URL). Keep the URL private.
3. In the Render service's environment settings, set `DATABASE_URL` to that
   PostgreSQL connection string. Do not put it in source control or share it in
   chat. The backend adds `sslmode=require` if the URL does not already specify
   an SSL mode.
4. The service creates its application tables on startup. A production startup
   fails unless `DATABASE_URL` uses PostgreSQL, so it will not silently fall back
   to an ephemeral SQLite database.
5. Redeploy and verify `/health`; check Render logs for a successful startup.
   Never paste the database URL into logs or screenshots.

The local developer default remains SQLite. Existing local SQLite data is not
automatically copied to Supabase; the new Supabase database starts with the
default `admin` account created from Render's `DEFAULT_PASSWORD`.

### Netlify frontend (Step 4)

The root `netlify.toml` is configured for this repository layout: it builds from
`frontend`, publishes `dist`, and rewrites app routes to `index.html`. To deploy:

1. In Netlify choose **Add new site → Import an existing project** and connect
   the GitHub repository. Netlify will detect the root `netlify.toml`.
2. Set these site environment variables before deploying:
   - `VITE_AUTH_REQUIRED=true`
   - `VITE_API_BASE_URL=https://YOUR-RENDER-SERVICE.onrender.com/api/v1`
3. Deploy and copy the Netlify site origin (for example,
   `https://YOUR-SITE.netlify.app`).
4. Set Render's `FRONTEND_URL` to the Netlify origin and redeploy the backend
   so its CORS allowlist and OAuth return URL use Netlify.
5. Redeploy on Netlify whenever its build environment variables change.

The Netlify site uses the Render API and Supabase database. Keep provider
secrets only in Render.

### Final testing (Step 5)

Run these checks after Netlify, Render, and Supabase are connected:

1. Open `https://YOUR-RENDER-SERVICE.onrender.com/health`; expect
   `{"status":"healthy"}`.
2. Open `https://YOUR-RENDER-SERVICE.onrender.com/docs`; expect the FastAPI
   documentation to load.
3. In a private/incognito browser, open the Netlify site. The sign-in screen
   should appear. Verify an unauthenticated request such as
   `GET /api/v1/scripts/` returns `401`, then sign in as `admin` using the
   `DEFAULT_PASSWORD` saved in Render.
4. Verify the dashboard loads, create and list a script, then reload the page
   and confirm the session stays signed in. Sign out and confirm the login
   screen returns.
5. In Supabase, verify the application tables exist after the backend has
   started. Create a test record through the app and confirm it persists after
   a Render restart/redeploy.
6. If testing media, generate a voice preview and confirm audio plays; video
   generation needs working external model/stock-footage services and persistent
   media storage. Do not treat ephemeral Render filesystem storage as durable.
7. Check the browser console and Render logs for CORS, 401/500, or database
   connection errors. Do not include passwords, tokens, or database URLs in
   screenshots or shared logs.

The local frontend production build was verified during development. End-to-end
cloud tests cannot pass until a GitHub remote, deployed Render URL, and Netlify
deployment are available.

---

## 9. Tech Stack Summary

- **Backend:** Python 3.12, FastAPI, SQLAlchemy, Pydantic, Ollama, Edge-TTS, MoviePy, Pillow, Google API Client  
- **Frontend:** React 18, Vite, Tailwind CSS, Lucide Icons, Recharts, Axios, React Router  
- **Access:** Local dashboard without sign-in; Google OAuth for YouTube  
- **DB:** SQLite (dev)  

---

## License & Responsibility

This project is for educational and personal automation.  
Respect YouTube Terms of Service, copyright, and platform policies.  
Only upload content you have rights to. Public publishing always requires explicit approval in the app.

---

**YouTube AI Command Center** — built as a complete, modular automation platform.
