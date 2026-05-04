import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Briefcase, Upload, FileText, LayoutDashboard, Menu, X } from 'lucide-react';

export default function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  const links = [
    { name: 'Home', path: '/', icon: Briefcase },
    { name: 'Upload Resume', path: '/upload', icon: Upload },
    { name: 'Job Description', path: '/job-description', icon: FileText },
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  ];

  return (
    <nav className="sticky top-0 z-50 w-full backdrop-blur-md bg-surface/80 border-b border-surface-hover shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex-shrink-0">
            <Link to="/" className="flex items-center gap-2">
              <div className="bg-gradient-to-tr from-primary to-secondary p-2 rounded-lg">
                <Briefcase className="h-6 w-6 text-white" />
              </div>
              <span className="font-bold text-xl tracking-tight text-text-main">
                AI Recruiter
              </span>
            </Link>
          </div>

          <div className="hidden md:flex md:items-center md:space-x-4">
            {links.map((link) => {
              const Icon = link.icon;
              const isActive = location.pathname === link.path;
              return (
                <Link
                  key={link.name}
                  to={link.path}
                  className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-surface-hover text-primary shadow-sm'
                      : 'text-text-muted hover:bg-surface-hover hover:text-text-main'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {link.name}
                </Link>
              );
            })}
          </div>

          <button
            type="button"
            className="inline-flex items-center justify-center rounded-md border border-surface-hover bg-surface/90 p-2 text-text-main transition hover:bg-surface-hover md:hidden"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-expanded={mobileOpen}
            aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>

        {mobileOpen && (
          <div className="mt-2 space-y-2 rounded-xl border border-surface-hover bg-surface/95 p-3 shadow-lg md:hidden">
            {links.map((link) => {
              const Icon = link.icon;
              const isActive = location.pathname === link.path;
              return (
                <Link
                  key={link.name}
                  to={link.path}
                  onClick={() => setMobileOpen(false)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-surface-hover text-primary shadow-sm'
                      : 'text-text-muted hover:bg-surface-hover hover:text-text-main'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {link.name}
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </nav>
  );
}
