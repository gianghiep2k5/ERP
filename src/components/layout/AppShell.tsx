import type { ReactNode } from 'react';
import Sidebar from './Sidebar';
import './AppShell.css';

/**
 * AppShell wraps all authenticated pages with the persistent sidebar.
 */
export default function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="appshell">
      <Sidebar />
      <main className="appshell-main">{children}</main>
    </div>
  );
}
