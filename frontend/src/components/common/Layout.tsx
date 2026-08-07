import { Outlet } from 'react-router-dom';
import { Navbar } from './Navbar';

/**
 * Application layout shell with persistent navigation bar.
 * Renders the Navbar at the top and page content below via Outlet.
 */
export function Layout() {
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <Navbar />
      <main>
        <Outlet />
      </main>
    </div>
  );
}
