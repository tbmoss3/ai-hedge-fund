import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { cn } from '@/lib/utils';
import { researchApi } from '@/services/research-api';
import { Investment, InvestmentFilters, Memo } from '@/types/research';
import {
  ArrowDown,
  ArrowUp,
  Briefcase,
  Download,
  Eye,
  Filter,
  Loader2,
  RefreshCw,
  SlidersHorizontal,
  X,
} from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

interface MemoDialogProps {
  memo: Memo | null;
  isOpen: boolean;
  onClose: () => void;
}

function MemoDialog({ memo, isOpen, onClose }: MemoDialogProps) {
  if (!isOpen || !memo) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <Card className="relative z-10 w-full max-w-2xl max-h-[80vh] overflow-auto m-4">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Original Investment Memo - {memo.ticker}</CardTitle>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="font-semibold mb-1">Thesis</h4>
            <p className="text-sm text-muted-foreground">{memo.thesis}</p>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h4 className="font-semibold mb-1 text-green-500">Bull Case</h4>
              <ul className="space-y-1">
                {memo.bull_case.map((point, i) => (
                  <li key={i} className="text-sm text-muted-foreground list-disc ml-4">
                    {point}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-1 text-red-500">Bear Case</h4>
              <ul className="space-y-1">
                {memo.bear_case.map((point, i) => (
                  <li key={i} className="text-sm text-muted-foreground list-disc ml-4">
                    {point}
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <div className="text-xs text-muted-foreground">
            Conviction: {memo.conviction}% | Target: ${memo.target_price.toFixed(2)} | Generated: {new Date(memo.generated_at).toLocaleDateString()}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

interface ClosePositionDialogProps {
  investment: Investment | null;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (id: string, exitPrice: number) => void;
}

function ClosePositionDialog({ investment, isOpen, onClose, onConfirm }: ClosePositionDialogProps) {
  const [exitPrice, setExitPrice] = useState('');

  useEffect(() => {
    if (investment?.current_price) {
      setExitPrice(investment.current_price.toFixed(2));
    }
  }, [investment]);

  if (!isOpen || !investment) return null;

  const handleConfirm = () => {
    const price = parseFloat(exitPrice);
    if (!isNaN(price) && price > 0) {
      onConfirm(investment.id, price);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <Card className="relative z-10 w-full max-w-md m-4">
        <CardHeader>
          <CardTitle>Close Position - {investment.ticker}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium">Exit Price</label>
            <Input
              type="number"
              step="0.01"
              value={exitPrice}
              onChange={(e) => setExitPrice(e.target.value)}
              placeholder="Enter exit price"
              className="mt-1"
            />
          </div>
          <div className="text-sm text-muted-foreground">
            Entry Price: ${investment.entry_price.toFixed(2)}
          </div>
          <div className="flex gap-2 justify-end">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button onClick={handleConfirm}>Close Position</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export function Investments() {
  const [investments, setInvestments] = useState<Investment[]>([]);
  const [analysts, setAnalysts] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  // Filter state
  const [statusFilter, setStatusFilter] = useState<'active' | 'closed' | ''>('');
  const [analystFilter, setAnalystFilter] = useState<string>('');

  // Dialog state
  const [selectedMemo, setSelectedMemo] = useState<Memo | null>(null);
  const [isMemoDialogOpen, setIsMemoDialogOpen] = useState(false);
  const [selectedInvestment, setSelectedInvestment] = useState<Investment | null>(null);
  const [isCloseDialogOpen, setIsCloseDialogOpen] = useState(false);

  const fetchInvestments = useCallback(async (showLoader = true) => {
    try {
      if (showLoader) setIsLoading(true);
      setError(null);

      const activeFilters: InvestmentFilters = {};
      if (statusFilter) activeFilters.status = statusFilter;
      if (analystFilter) activeFilters.analyst = analystFilter;

      const data = await researchApi.getInvestments(activeFilters);
      setInvestments(data);
    } catch (err) {
      setError('Failed to load investments. Please try again.');
      console.error('Error fetching investments:', err);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [statusFilter, analystFilter]);

  const fetchAnalysts = useCallback(async () => {
    try {
      const data = await researchApi.getAnalysts();
      setAnalysts(data);
    } catch (err) {
      console.error('Error fetching analysts:', err);
    }
  }, []);

  useEffect(() => {
    fetchInvestments();
    fetchAnalysts();
  }, [fetchInvestments, fetchAnalysts]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    fetchInvestments(false);
  };

  const handleViewMemo = async (memoId: string) => {
    try {
      const memo = await researchApi.getMemo(memoId);
      setSelectedMemo(memo);
      setIsMemoDialogOpen(true);
    } catch (err) {
      console.error('Error fetching memo:', err);
    }
  };

  const handleClosePosition = (investment: Investment) => {
    setSelectedInvestment(investment);
    setIsCloseDialogOpen(true);
  };

  const handleConfirmClose = async (id: string, exitPrice: number) => {
    try {
      await researchApi.closeInvestment(id, exitPrice);
      fetchInvestments(false);
    } catch (err) {
      console.error('Error closing position:', err);
      setError('Failed to close position. Please try again.');
    }
  };

  const clearFilters = () => {
    setStatusFilter('');
    setAnalystFilter('');
  };

  const hasActiveFilters = statusFilter || analystFilter;

  const exportToCsv = () => {
    const headers = [
      'Ticker',
      'Analyst',
      'Signal',
      'Entry Date',
      'Entry Price',
      'Current Price',
      'Exit Price',
      'Exit Date',
      'P&L %',
      'Status',
    ];

    const rows = investments.map((inv) => [
      inv.ticker,
      inv.analyst,
      inv.signal,
      inv.entry_date,
      inv.entry_price.toFixed(2),
      inv.current_price?.toFixed(2) || '',
      inv.exit_price?.toFixed(2) || '',
      inv.exit_date || '',
      inv.pnl_percent?.toFixed(2) || '',
      inv.status,
    ]);

    const csvContent = [headers.join(','), ...rows.map((row) => row.join(','))].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `investments_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
  };

  const formatPrice = (price: number | undefined) => {
    if (price === undefined) return '-';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(price);
  };

  const formatPnl = (pnl: number | undefined) => {
    if (pnl === undefined) return '-';
    const isPositive = pnl >= 0;
    return (
      <span className={cn('flex items-center gap-1', isPositive ? 'text-green-500' : 'text-red-500')}>
        {isPositive ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />}
        {Math.abs(pnl).toFixed(2)}%
      </span>
    );
  };

  // Calculate summary stats
  const activePositions = investments.filter((i) => i.status === 'active');
  const closedPositions = investments.filter((i) => i.status === 'closed');
  const totalPnl = closedPositions.reduce((sum, i) => sum + (i.pnl_percent || 0), 0);
  const avgPnl = closedPositions.length > 0 ? totalPnl / closedPositions.length : 0;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center gap-3">
          <Briefcase className="h-6 w-6" />
          <h1 className="text-xl font-semibold">Portfolio</h1>
          <Badge variant="secondary" className="text-sm">
            {activePositions.length} active
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
          </Button>
          <Button variant="outline" size="sm" onClick={exportToCsv}>
            <Download className="h-4 w-4 mr-2" />
            Export CSV
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

      {/* Summary cards */}
      <div className="grid grid-cols-4 gap-4 p-4 border-b">
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-muted-foreground">Active Positions</div>
            <div className="text-2xl font-bold">{activePositions.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-muted-foreground">Closed Positions</div>
            <div className="text-2xl font-bold">{closedPositions.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-muted-foreground">Total Return</div>
            <div className={cn('text-2xl font-bold', totalPnl >= 0 ? 'text-green-500' : 'text-red-500')}>
              {totalPnl >= 0 ? '+' : ''}{totalPnl.toFixed(2)}%
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-muted-foreground">Avg Return</div>
            <div className={cn('text-2xl font-bold', avgPnl >= 0 ? 'text-green-500' : 'text-red-500')}>
              {avgPnl >= 0 ? '+' : ''}{avgPnl.toFixed(2)}%
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters panel */}
      {showFilters && (
        <div className="p-4 border-b bg-muted/30">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Filters:</span>
            </div>

            {/* Status filter */}
            <div className="flex items-center gap-2">
              <label className="text-sm text-muted-foreground">Status:</label>
              <div className="flex gap-1">
                <Button
                  variant={statusFilter === '' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setStatusFilter('')}
                  className="h-8"
                >
                  All
                </Button>
                <Button
                  variant={statusFilter === 'active' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setStatusFilter('active')}
                  className="h-8"
                >
                  Active
                </Button>
                <Button
                  variant={statusFilter === 'closed' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setStatusFilter('closed')}
                  className="h-8"
                >
                  Closed
                </Button>
              </div>
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

            {/* Clear button */}
            {hasActiveFilters && (
              <Button variant="ghost" size="sm" onClick={clearFilters} className="ml-auto">
                <X className="h-4 w-4 mr-1" />
                Clear
              </Button>
            )}
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
              <Button onClick={() => fetchInvestments()}>Try Again</Button>
            </CardContent>
          </Card>
        ) : investments.length === 0 ? (
          <Card>
            <CardHeader>
              <CardTitle className="text-center text-muted-foreground">
                <Briefcase className="h-12 w-12 mx-auto mb-4 opacity-50" />
                No Investments
              </CardTitle>
            </CardHeader>
            <CardContent className="text-center text-muted-foreground">
              {hasActiveFilters ? (
                <p>No investments match your current filters.</p>
              ) : (
                <p>Approve memos from the Inbox to start building your portfolio.</p>
              )}
            </CardContent>
          </Card>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Ticker</TableHead>
                <TableHead>Analyst</TableHead>
                <TableHead>Signal</TableHead>
                <TableHead>Entry Date</TableHead>
                <TableHead className="text-right">Entry Price</TableHead>
                <TableHead className="text-right">Current Price</TableHead>
                <TableHead className="text-right">P&L</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {investments.map((investment) => (
                <TableRow key={investment.id} className="cursor-pointer hover:bg-muted/50">
                  <TableCell className="font-medium">{investment.ticker}</TableCell>
                  <TableCell>{investment.analyst}</TableCell>
                  <TableCell>
                    <Badge
                      variant={investment.signal === 'bullish' ? 'success' : 'destructive'}
                      className="text-xs"
                    >
                      {investment.signal.toUpperCase()}
                    </Badge>
                  </TableCell>
                  <TableCell>{new Date(investment.entry_date).toLocaleDateString()}</TableCell>
                  <TableCell className="text-right">{formatPrice(investment.entry_price)}</TableCell>
                  <TableCell className="text-right">
                    {investment.status === 'closed'
                      ? formatPrice(investment.exit_price)
                      : formatPrice(investment.current_price)}
                  </TableCell>
                  <TableCell className="text-right">{formatPnl(investment.pnl_percent)}</TableCell>
                  <TableCell>
                    <Badge variant={investment.status === 'active' ? 'success' : 'secondary'}>
                      {investment.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleViewMemo(investment.memo_id)}
                        title="View original memo"
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                      {investment.status === 'active' && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleClosePosition(investment)}
                        >
                          Close
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      {/* Dialogs */}
      <MemoDialog
        memo={selectedMemo}
        isOpen={isMemoDialogOpen}
        onClose={() => setIsMemoDialogOpen(false)}
      />
      <ClosePositionDialog
        investment={selectedInvestment}
        isOpen={isCloseDialogOpen}
        onClose={() => setIsCloseDialogOpen(false)}
        onConfirm={handleConfirmClose}
      />
    </div>
  );
}
