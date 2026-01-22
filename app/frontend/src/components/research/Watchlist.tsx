import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { researchApi } from '@/services/research-api';
import { Watchlist as WatchlistType } from '@/types/research';
import {
  Eye,
  Loader2,
  Plus,
  RefreshCw,
  Trash2,
  X,
} from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

export function Watchlist() {
  const [watchlist, setWatchlist] = useState<WatchlistType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isAdding, setIsAdding] = useState(false);
  const [removingTicker, setRemovingTicker] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tickerInput, setTickerInput] = useState('');

  const fetchWatchlist = useCallback(async (showLoader = true) => {
    try {
      if (showLoader) setIsLoading(true);
      setError(null);
      const data = await researchApi.getWatchlist();
      setWatchlist(data);
    } catch (err) {
      setError('Failed to load watchlist. Please try again.');
      console.error('Error fetching watchlist:', err);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchWatchlist();
  }, [fetchWatchlist]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    fetchWatchlist(false);
  };

  const handleAddTickers = async () => {
    if (!tickerInput.trim()) return;

    try {
      setIsAdding(true);
      // Parse input: support comma-separated, space-separated, or both
      const tickers = tickerInput
        .split(/[\s,]+/)
        .map((t) => t.trim().toUpperCase())
        .filter((t) => t.length > 0);

      if (tickers.length === 0) return;

      const updated = await researchApi.addTickers(tickers);
      setWatchlist(updated);
      setTickerInput('');
    } catch (err) {
      console.error('Error adding tickers:', err);
      setError('Failed to add tickers. Please try again.');
    } finally {
      setIsAdding(false);
    }
  };

  const handleRemoveTicker = async (ticker: string) => {
    try {
      setRemovingTicker(ticker);
      const updated = await researchApi.removeTickers([ticker]);
      setWatchlist(updated);
    } catch (err) {
      console.error('Error removing ticker:', err);
      setError('Failed to remove ticker. Please try again.');
    } finally {
      setRemovingTicker(null);
    }
  };

  const handleClearAll = async () => {
    if (!confirm('Are you sure you want to clear all tickers from your watchlist?')) {
      return;
    }

    try {
      setIsLoading(true);
      const updated = await researchApi.clearWatchlist();
      setWatchlist(updated);
    } catch (err) {
      console.error('Error clearing watchlist:', err);
      setError('Failed to clear watchlist. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleAddTickers();
    }
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'Never';
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center gap-3">
          <Eye className="h-6 w-6" />
          <h1 className="text-xl font-semibold">Watchlist</h1>
          <Badge variant="secondary" className="text-sm">
            {watchlist?.tickers?.length || 0} tickers
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          {watchlist && watchlist.tickers.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleClearAll}
              className="text-destructive hover:text-destructive"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Clear All
            </Button>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Add tickers panel */}
      <div className="p-4 border-b bg-muted/30">
        <div className="flex items-center gap-4">
          <div className="flex-1 flex items-center gap-2">
            <Input
              placeholder="Enter tickers (e.g., AAPL, MSFT, NVDA)"
              value={tickerInput}
              onChange={(e) => setTickerInput(e.target.value)}
              onKeyDown={handleKeyDown}
              className="flex-1"
              disabled={isAdding}
            />
            <Button onClick={handleAddTickers} disabled={isAdding || !tickerInput.trim()}>
              {isAdding ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Plus className="h-4 w-4 mr-2" />
              )}
              Add
            </Button>
          </div>
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          Separate multiple tickers with commas or spaces
        </p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4">
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : error ? (
          <Card className="border-destructive">
            <CardContent className="flex flex-col items-center justify-center py-8">
              <p className="text-destructive mb-4">{error}</p>
              <Button onClick={() => fetchWatchlist()}>Try Again</Button>
            </CardContent>
          </Card>
        ) : !watchlist || watchlist.tickers.length === 0 ? (
          <Card>
            <CardHeader>
              <CardTitle className="text-center text-muted-foreground">
                <Eye className="h-12 w-12 mx-auto mb-4 opacity-50" />
                Your Watchlist is Empty
              </CardTitle>
            </CardHeader>
            <CardContent className="text-center text-muted-foreground">
              <p>Add stock tickers above to start monitoring them.</p>
              <p className="mt-2 text-sm">
                The system will automatically scan your watchlist on the 1st of each month.
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="max-w-4xl mx-auto">
            {/* Last scan info */}
            <Card className="mb-4">
              <CardContent className="py-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Last Scan:</span>
                  <span className="font-medium">{formatDate(watchlist.last_scan_at)}</span>
                </div>
                <div className="flex items-center justify-between text-sm mt-2">
                  <span className="text-muted-foreground">Next Scheduled Scan:</span>
                  <span className="font-medium">1st of next month at 6:00 AM UTC</span>
                </div>
              </CardContent>
            </Card>

            {/* Tickers grid */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Tickers ({watchlist.tickers.length})</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {watchlist.tickers.map((ticker) => (
                    <Badge
                      key={ticker}
                      variant="secondary"
                      className="text-sm py-1.5 px-3 flex items-center gap-2"
                    >
                      <span className="font-mono font-semibold">{ticker}</span>
                      <button
                        onClick={() => handleRemoveTicker(ticker)}
                        disabled={removingTicker === ticker}
                        className="hover:text-destructive transition-colors"
                      >
                        {removingTicker === ticker ? (
                          <Loader2 className="h-3 w-3 animate-spin" />
                        ) : (
                          <X className="h-3 w-3" />
                        )}
                      </button>
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
