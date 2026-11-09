import { Outlet, NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, FileText, Mic, Video, Image, Youtube, Upload,
  Calendar, Settings, History, Key, User, Menu, X, Sparkles, Laptop
} from 'lucide-react'
import { useState } from 'react'
import clsx from 'clsx'
import { useAuth } from '../context/AuthContext'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Overview' },
  { to: '/scripts', icon: FileText, label: 'Script Studio' },
  { to: '/voice', icon: Mic, label: 'Voice Studio' },
  { to: '/videos', icon: Video, label: 'Video Generator' },
  { to: '/thumbnails', icon: Image, label: 'Thumbnails' },
  { to: '/youtube', icon: Youtube, label: 'YouTube Channel' },
  { to: '/uploads', icon: Upload, label: 'Upload Manager' },
  { to: '/calendar', icon: Calendar, label: 'Content Ideas' },
  { to: '/automation', icon: Settings, label: 'Automation' },
  { to: '/history', icon: History, label: 'History & Logs' },
  { to: '/api-settings', icon: Key, label: 'API Settings' },
  { to: '/profile', icon: User, label: 'Profile' },
]

export default function DashboardLayout() {
  const [open, setOpen] = useState(false)
  const location = useLocation()
  const { user } = useAuth()
  const currentPage = navItems.find((item) => item.to === location.pathname)?.label || 'Workspace'

  return (
    <div className="min-h-screen flex" style={{ position: 'relative' }}>
      {open && <button className="yc-overlay lg:hidden" aria-label="Close navigation" onClick={() => setOpen(false)} />}

      <aside className={clsx('yc-sidebar', open && 'open')}>
        <div className="yc-brand">
          <div className="yc-logo">
            <Sparkles size={22} color="#020617" strokeWidth={2.5} />
          </div>
          <div>
            <div className="yc-brand-title">YOUTUBE AI</div>
            <div className="yc-brand-sub">Command Center</div>
          </div>
          <button className="lg:hidden ml-auto text-slate-400" aria-label="Close navigation" onClick={() => setOpen(false)}>
            <X size={20} />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto py-3" aria-label="Main navigation">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              onClick={() => setOpen(false)}
              className={({ isActive }) => clsx('yc-nav-item', isActive && 'active')}
            >
              <Icon size={17} strokeWidth={1.8} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="yc-workspace-label">
          <div className="yc-workspace-icon">
            <Laptop size={18} />
          </div>
          <div style={{ minWidth: 0 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: '#fff' }}>{user?.username || 'Local workspace'}</div>
            <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>No sign-in required</div>
          </div>
        </div>
      </aside>

      <div className="yc-main">
        <header className="yc-topbar">
          <button className="yc-menu-button lg:hidden" aria-label="Open navigation" onClick={() => setOpen(true)}>
            <Menu size={22} />
          </button>
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className="yc-topbar-label">Workspace</span>
            <span className="yc-topbar-separator">/</span>
            <span className="yc-topbar-page">{currentPage}</span>
          </div>
          <span className="yc-pill yc-pill-workspace">
            <Laptop size={13} /> Local
          </span>
        </header>

        <div className="yc-content">
          <div className="yc-animate">
            <Outlet />
          </div>
        </div>
      </div>
    </div>
  )
}
