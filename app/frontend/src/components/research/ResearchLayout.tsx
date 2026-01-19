import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { researchApi } from '@/services/research-api';
import {
  Briefcase,
  Inbox as InboxIcon,
  Menu,
  Moon,
  Sun,
  Trophy,
  X,
} from 'lucide-react';
import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';
import { Inbox } from './Inbox';
import { Investments } from './Investments';
import { Leaderboard } from './Leaderboard';

type View = 'inbox' | 'investments' | 'leaderboard';

interface NavItem {
  id: View;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const navItems: NavItem[] = [
  { id: 'inbox', label: 'Inbox', icon: InboxIcon },
  { id: 'investments', label: 'Portfolio', icon: Briefcase },
  { id: 'leaderboard', label: 'Leaderboard', icon: Trophy },
];

export function ResearchLayout() {
  const [currentView, setCurrentView] = useState<View>('inbox');
  const [inboxCount, setInboxCount] = useState<number>(0);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // Prevent hydration mismatch
  useEffect(() => {
    setMounted(true);
  }, []);

  const isDarkMode = mounted && resolvedTheme === 'dark';

  // Fetch inbox count for badge
  useEffect(() => {
    const fetchCount = async () => {
      try {
        const count = await researchApi.getInboxCount();
        setInboxCount(count);
      } catch (err) {
        console.error('Error fetching inbox count:', err);
      }
    };
    fetchCount();

    // Refresh count every 30 seconds
    const interval = setInterval(fetchCount, 30000);
    return () => clearInterval(interval);
  }, []);

  // Update inbox count when view changes to inbox
  useEffect(() => {
    if (currentView === 'inbox') {
      const fetchCount = async () => {
        try {
          const count = await researchApi.getInboxCount();
          setInboxCount(count);
        } catch (err) {
          console.error('Error fetching inbox count:', err);
        }
      };
      fetchCount();
    }
  }, [currentView]);

  const toggleDarkMode = () => {
    setTheme(isDarkMode ? 'light' : 'dark');
  };

  const renderView = () => {
    switch (currentView) {
      case 'inbox':
        return <Inbox />;
      case 'investments':
        return <Investments />;
      case 'leaderboard':
        return <Leaderboard />;
      default:
        return <Inbox />;
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background">
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex flex-col w-64 border-r bg-card">
        {/* Logo/Brand */}
        <div className="flex items-center gap-2 p-4 border-b">
          <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
            <Trophy className="h-5 w-5 text-primary-foreground" />
          </div>
          <div>
            <h1 className="font-semibold">Research Hub</h1>
            <p className="text-xs text-muted-foreground">Investment Review Platform</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-2">
          <ul className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentView === item.id;
              return (
                <li key={item.id}>
                  <button
                    onClick={() => setCurrentView(item.id)}
                    className={cn(
                      'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-primary text-primary-foreground'
                        : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                    )}
                  >
                    <Icon className="h-5 w-5" />
                    <span>{item.label}</span>
                    {item.id === 'inbox' && inboxCount > 0 && (
                      <Badge
                        variant={isActive ? 'secondary' : 'destructive'}
                        className="ml-auto h-5 min-w-5 flex items-center justify-center"
                      >
                        {inboxCount}
                      </Badge>
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Footer */}
        <div className="p-4 border-t">
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start"
            onClick={toggleDarkMode}
          >
            {isDarkMode ? (
              <Sun className="h-4 w-4 mr-2" />
            ) : (
              <Moon className="h-4 w-4 mr-2" />
            )}
            {isDarkMode ? 'Light Mode' : 'Dark Mode'}
          </Button>
        </div>
      </aside>

      {/* Mobile Header */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-40 bg-card border-b">
        <div className="flex items-center justify-between p-3">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
              <Trophy className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="font-semibold">Research Hub</span>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={toggleDarkMode}>
              {isDarkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            >
              {isMobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </Button>
          </div>
        </div>

        {/* Mobile Navigation Menu */}
        {isMobileMenuOpen && (
          <nav className="p-2 border-t bg-card">
            <ul className="space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = currentView === item.id;
                return (
                  <li key={item.id}>
                    <button
                      onClick={() => {
                        setCurrentView(item.id);
                        setIsMobileMenuOpen(false);
                      }}
                      className={cn(
                        'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                        isActive
                          ? 'bg-primary text-primary-foreground'
                          : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                      )}
                    >
                      <Icon className="h-5 w-5" />
                      <span>{item.label}</span>
                      {item.id === 'inbox' && inboxCount > 0 && (
                        <Badge
                          variant={isActive ? 'secondary' : 'destructive'}
                          className="ml-auto h-5 min-w-5 flex items-center justify-center"
                        >
                          {inboxCount}
                        </Badge>
                      )}
                    </button>
                  </li>
                );
              })}
            </ul>
          </nav>
        )}
      </div>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden md:pt-0 pt-14">
        {renderView()}
      </main>
    </div>
  );
}
