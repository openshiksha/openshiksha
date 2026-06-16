import { BottomNav } from './BottomNav';
import { Navbar } from './Navbar';
import { OfflineBanner } from './OfflineBanner';
import { InstallBanner } from '@/features/pwa/InstallBanner';
import { PendingSyncBadge } from '@/features/student/SyncStatus';

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell = ({ children }: AppShellProps) => (
  <div className="bg-paper min-h-screen min-h-[100dvh]">
    {/* Skip link — visually hidden until focused, then anchors at top-left.
        Lets keyboard / screen-reader users jump past the Navbar to page content. */}
    <a
      href="#main-content"
      className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-3 focus:z-50 focus:rounded-md focus:bg-brand-600 focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-white focus:shadow-lift focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-300"
    >
      Skip to main content
    </a>
    <Navbar />
    <OfflineBanner />
    <PendingSyncBadge />
    <InstallBanner />
    <main
      id="main-content"
      tabIndex={-1}
      className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8 py-5 sm:py-8 pb-[calc(6.75rem+env(safe-area-inset-bottom))] sm:pb-8 focus-visible:outline-none"
    >
      {children}
    </main>
    <BottomNav />
  </div>
);
