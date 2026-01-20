import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import { researchApi } from '@/services/research-api';
import { InboxFilters, Memo } from '@/types/research';
import {
  Filter,
  Inbox as InboxIcon,
  Loader2,
  RefreshCw,
  SlidersHorizontal,
  TrendingDown,
  TrendingUp,
  X,
} from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { MemoCard } from './MemoCard';

export function Inbox() {
  const [memos, setMemos] = useState<Memo[]>([]);
  const [analysts, setAnalysts] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  // Filter state
  const [filters, setFilters] = useState<InboxFilters>({});
  const [analystFilter, setAnalystFilter] = useState<string>('');
  const [signalFilter, setSignalFilter] = useState<'bullish' | 'bearish' | ''>('');
  const [minConviction, setMinConviction] = useState<string>('');

  const fetchMemos = useCallback(async (showLoader = true) => {
    try {
      if (showLoader) setIsLoading(true);
      setError(null);

      const activeFilters: InboxFilters = {};
      if (analystFilter) activeFilters.analyst = analystFilter;
      if (signalFilter) activeFilters.signal = signalFilter;
      if (minConviction && !isNaN(Number(minConviction))) {
        activeFilters.minConviction = Number(minConviction);
      }

      const response = await researchApi.getInbox(activeFilters);
      // Handle both array and {items: []} response formats
      const data = Array.isArray(response) ? response : (response as any).items || [];
      // Sort by conviction (highest first)
      const sortedMemos = data.sort((a, b) => b.conviction - a.conviction);
      setMemos(sortedMemos);
    } catch (err) {
      setError('Failed to load memos. Please try again.');
      console.error('Error fetching memos:', err);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [analystFilter, signalFilter, minConviction]);

  const fetchAnalysts = useCallback(async () => {
    try {
      const data = await researchApi.getAnalysts();
      setAnalysts(data);
    } catch (err) {
      console.error('Error fetching analysts:', err);
    }
  }, []);

  useEffect(() => {
    fetchMemos();
    fetchAnalysts();
  }, [fetchMemos, fetchAnalysts]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    fetchMemos(false);
  };

  const handleApprove = async (id: string) => {
    try {
      setActionLoading(id);
      await researchApi.approveMemo(id);
      // Remove the memo from the list after approval
      setMemos((prev) => prev.filter((memo) => memo.id !== id));
    } catch (err) {
      console.error('Error approving memo:', err);
      setError('Failed to approve memo. Please try again.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (id: string) => {
    try {
      setActionLoading(id);
      await researchApi.rejectMemo(id);
      // Remove the memo from the list after rejection
      setMemos((prev) => prev.filter((memo) => memo.id !== id));
    } catch (err) {
      console.error('Error rejecting memo:', err);
      setError('Failed to reject memo. Please try again.');
    } finally {
      setActionLoading(null);
    }
  };

  const clearFilters = () => {
    setAnalystFilter('');
    setSignalFilter('');
    setMinConviction('');
  };

  const hasActiveFilters = analystFilter || signalFilter || minConviction;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center gap-3">
          <InboxIcon className="h-6 w-6" />
          <h1 className="text-xl font-semibold">Memo Inbox</h1>
          <Badge variant="secondary" className="text-sm">
            {memos.length} pending
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
            className={cn(showFilters && 'bg-accent')}
          >
            <SlidersHorizontal className="h-4 w-4 mr-2" />
            Filters
            {hasActiveFilters && (
              <Badge variant="destructive" className="ml-2 h-5 w-5 p-0 flex items-center justify-center">
                !
              </Badge>
            )}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw className={cn('h-4 w-4 mr-2', isRefreshing && 'animate-spin')} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Filters panel */}
      {showFilters && (
        <div className="p-4 border-b bg-muted/30">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Filters:</span>
            </div>

            {/* Analyst filter */}
            <div className="flex items-center gap-2">
              <label className="text-sm text-muted-foreground">Analyst:</label>
              <select
                value={analystFilter}
                onChange={(e) => setAnalystFilter(e.target.value)}
                className="h-8 px-2 rounded-md border border-border bg-background text-sm"
              >
                <option value="">All</option>
                {analysts.map((analyst) => (
                  <option key={analyst} value={analyst}>
                    {analyst}
                  </option>
                ))}
              </select>
            </div>

            {/* Signal filter */}
            <div className="flex items-center gap-2">
              <label className="text-sm text-muted-foreground">Signal:</label>
              <div className="flex gap-1">
                <Button
                  variant={signalFilter === '' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSignalFilter('')}
                  className="h-8"
                >
                  All
                </Button>
                <Button
                  variant={signalFilter === 'bullish' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSignalFilter('bullish')}
                  className={cn('h-8', signalFilter === 'bullish' && 'bg-green-500 hover:bg-green-600')}
                >
                  <TrendingUp className="h-3 w-3 mr-1" />
                  Bullish
                </Button>
                <Button
                  variant={signalFilter === 'bearish' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSignalFilter('bearish')}
                  className={cn('h-8', signalFilter === 'bearish' && 'bg-red-500 hover:bg-red-600')}
                >
                  <TrendingDown className="h-3 w-3 mr-1" />
                  Bearish
                </Button>
              </div>
            </div>

            {/* Min conviction filter */}
            <div className="flex items-center gap-2">
              <label className="text-sm text-muted-foreground">Min Conviction:</label>
              <Input
                type="number"
                min="0"
                max="100"
                placeholder="e.g. 70"
                value={minConviction}
                onChange={(e) => setMinConviction(e.target.value)}
                className="h-8 w-20"
              />
              <span className="text-sm text-muted-foreground">%</span>
            </div>

            {/* Apply and clear buttons */}
            <div className="flex gap-2 ml-auto">
              {hasActiveFilters && (
                <Button variant="ghost" size="sm" onClick={clearFilters}>
                  <X className="h-4 w-4 mr-1" />
                  Clear
                </Button>
              )}
              <Button size="sm" onClick={() => fetchMemos()}>
                Apply
              </Button>
            </div>
          </div>
        </div>
      )}

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
              <Button onClick={() => fetchMemos()}>Try Again</Button>
            </CardContent>
          </Card>
        ) : memos.length === 0 ? (
          <Card>
            <CardHeader>
              <CardTitle className="text-center text-muted-foreground">
                <InboxIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
                No Pending Memos
              </CardTitle>
            </CardHeader>
            <CardContent className="text-center text-muted-foreground">
              {hasActiveFilters ? (
                <p>No memos match your current filters. Try adjusting your criteria.</p>
              ) : (
                <p>All memos have been reviewed. Check back later for new research.</p>
              )}
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4 max-w-4xl mx-auto">
            {memos.map((memo) => (
              <MemoCard
                key={memo.id}
                memo={memo}
                onApprove={handleApprove}
                onReject={handleReject}
                isLoading={actionLoading === memo.id}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
