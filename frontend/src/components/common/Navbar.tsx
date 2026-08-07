import { Link, useLocation } from 'react-router-dom';
import {
  SignedIn,
  SignedOut,
  SignInButton,
  UserButton,
} from '@clerk/clerk-react';

/**
 * Navigation bar with mode links and auth state.
 * Displays links to Home, Play modes (Daily/Quick Play), Leaderboard, and Profile.
 * Shows sign-in button for unauthenticated users and user avatar for authenticated users.
 *
 * Requirements: 14.2, 14.3
 */
export function Navbar() {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;
  const isPlayActive = location.pathname.startsWith('/play');

  return (
    <nav
      className="sticky top-0 z-50 bg-gray-900/95 backdrop-blur-sm border-b border-gray-800"
      aria-label="Main navigation"
    >
      <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
        {/* Left: Brand + Nav Links */}
        <div className="flex items-center gap-6">
          <Link
            to="/"
            className="text-nba-gold font-bold text-lg tracking-tight"
            aria-label="Hot Take home"
          >
            🏀 Hot Take
          </Link>

          <div className="hidden sm:flex items-center gap-1">
            <NavLink to="/" active={isActive('/')}>
              Home
            </NavLink>
            <NavDropdown label="Play" active={isPlayActive}>
              <DropdownLink to="/play/daily">Daily Challenge</DropdownLink>
              <DropdownLink to="/play/quickplay">Quick Play</DropdownLink>
              <DropdownLink to="/play/hoopiq">HoopIQ</DropdownLink>
            </NavDropdown>
            <NavLink to="/leaderboard" active={isActive('/leaderboard')}>
              Leaderboard
            </NavLink>
          </div>
        </div>

        {/* Right: Auth State */}
        <div className="flex items-center gap-3">
          <SignedIn>
            <NavLink to="/profile" active={isActive('/profile')}>
              Profile
            </NavLink>
            <UserButton
              afterSignOutUrl="/"
              appearance={{
                elements: {
                  avatarBox: 'w-8 h-8',
                },
              }}
            />
          </SignedIn>
          <SignedOut>
            <SignInButton mode="modal">
              <button className="px-3 py-1.5 text-sm font-medium text-gray-900 bg-nba-gold rounded-lg hover:bg-yellow-400 transition-colors">
                Sign In
              </button>
            </SignInButton>
          </SignedOut>

          {/* Mobile menu button */}
          <MobileMenu />
        </div>
      </div>
    </nav>
  );
}

function NavLink({
  to,
  active,
  children,
}: {
  to: string;
  active: boolean;
  children: React.ReactNode;
}) {
  return (
    <Link
      to={to}
      className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
        active
          ? 'text-nba-gold bg-gray-800'
          : 'text-gray-300 hover:text-white hover:bg-gray-800/50'
      }`}
    >
      {children}
    </Link>
  );
}

function NavDropdown({
  label,
  active,
  children,
}: {
  label: string;
  active: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="relative group">
      <button
        className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
          active
            ? 'text-nba-gold bg-gray-800'
            : 'text-gray-300 hover:text-white hover:bg-gray-800/50'
        }`}
        aria-haspopup="true"
      >
        {label} ▾
      </button>
      <div
        className="absolute left-0 top-full mt-1 w-40 py-1 bg-gray-800 border border-gray-700 rounded-lg shadow-xl
                   opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-150"
        role="menu"
      >
        {children}
      </div>
    </div>
  );
}

function DropdownLink({
  to,
  children,
}: {
  to: string;
  children: React.ReactNode;
}) {
  return (
    <Link
      to={to}
      className="block px-4 py-2 text-sm text-gray-300 hover:text-white hover:bg-gray-700/50 transition-colors"
      role="menuitem"
    >
      {children}
    </Link>
  );
}

function MobileMenu() {
  return (
    <div className="sm:hidden relative group">
      <button
        className="p-2 text-gray-400 hover:text-white"
        aria-label="Open mobile menu"
        aria-haspopup="true"
      >
        <svg
          className="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 6h16M4 12h16M4 18h16"
          />
        </svg>
      </button>
      <div
        className="absolute right-0 top-full mt-1 w-48 py-1 bg-gray-800 border border-gray-700 rounded-lg shadow-xl
                   opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-150"
        role="menu"
      >
        <DropdownLink to="/">Home</DropdownLink>
        <DropdownLink to="/play/daily">Daily Challenge</DropdownLink>
        <DropdownLink to="/play/quickplay">Quick Play</DropdownLink>
        <DropdownLink to="/play/hoopiq">HoopIQ</DropdownLink>
        <DropdownLink to="/leaderboard">Leaderboard</DropdownLink>
        <DropdownLink to="/profile">Profile</DropdownLink>
      </div>
    </div>
  );
}
