import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
import { AnalystStats, LeaderboardSortBy } from '@/types/research';
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  Crown,
  Loader2,
  Medal,
  RefreshCw,
  Trophy,
  User,
} from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

export function Leaderboard() {
  const [analysts, setAnalysts] = useState<AnalystStats[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<LeaderboardSortBy>('win_rate');

  const fetchLeaderboard = useCallback(async (showLoader = true) => {
    try {
      if (showLoader) setIsLoading(true);
      setError(null);
      const data = await researchApi.getLeaderboard(sortBy);
      setAnalysts(data);
    } catch (err) {
      setError('Failed to load leaderboard. Please try again.');
      console.error('Error fetching leaderboard:', err);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [sortBy]);

  useEffect(() => {
    fetchLeaderboard();
  }, [fetchLeaderboard]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    fetchLeaderboard(false);
  };

  const handleSort = (newSortBy: LeaderboardSortBy) => {
    setSortBy(newSortBy);
  };

  const getRankIcon = (index: number) => {
    switch (index) {
      case 0:
        return <Crown className="h-5 w-5 text-yellow-500" />;
      case 1:
        return <Medal className="h-5 w-5 text-gray-400" />;
      case 2:
        return <Medal className="h-5 w-5 text-amber-600" />;
      default:
        return <span className="w-5 text-center text-muted-foreground">{index + 1}</span>;
    }
  };

  const formatPercent = (value: number, showSign = false) => {
    const formatted = value.toFixed(1);
    if (showSign && value > 0) return `+${formatted}%`;
    return `${formatted}%`;
  };

  // Calculate overall stats
  const totalMemos = analysts.reduce((sum, a) => sum + a.total_memos, 0);
  const totalApproved = analysts.reduce((sum, a) => sum + a.approved_count, 0);
  const avgWinRate = analysts.length > 0
    ? analysts.reduce((sum, a) => sum + a.win_rate, 0) / analysts.length
    : 0;
  const avgReturn = analysts.length > 0
    ? analysts.reduce((sum, a) => sum + a.avg_return, 0) / analysts.length
    : 0;

  const sortOptions: { key: LeaderboardSortBy; label: string }[] = [
    { key: 'win_rate', label: 'Win Rate' },
    { key: 'avg_return', label: 'Avg Return' },
    { key: 'total_memos', label: 'Total Ideas' },
  ];

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center gap-3">
          <Trophy className="h-6 w-6" />
          <h1 className="text-xl font-semibold">Analyst Leaderboard</h1>
        </div>
        <div className="flex items-center gap-2">
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

      {/* Summary stats */}
      <div className="grid grid-cols-4 gap-4 p-4 border-b">
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-muted-foreground">Total Analysts</div>
            <div className="text-2xl font-bold">{analysts.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-muted-foreground">Total Ideas</div>
            <div className="text-2xl font-bold">{totalMemos}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-muted-foreground">Avg Win Rate</div>
            <div className="text-2xl font-bold">{formatPercent(avgWinRate)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-muted-foreground">Avg Return</div>
            <div className={cn('text-2xl font-bold', avgReturn >= 0 ? 'text-green-500' : 'text-red-500')}>
              {formatPercent(avgReturn, true)}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Sort options */}
      <div className="flex items-center gap-4 p-4 border-b bg-muted/30">
        <span className="text-sm font-medium">Sort by:</span>
        <div className="flex gap-2">
          {sortOptions.map((option) => (
            <Button
              key={option.key}
              variant={sortBy === option.key ? 'default' : 'outline'}
              size="sm"
              onClick={() => handleSort(option.key)}
            >
              <ArrowUpDown className="h-3 w-3 mr-1" />
              {option.label}
            </Button>
          ))}
        </div>
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
              <Button onClick={() => fetchLeaderboard()}>Try Again</Button>
            </CardContent>
          </Card>
        ) : analysts.length === 0 ? (
          <Card>
            <CardHeader>
              <CardTitle className="text-center text-muted-foreground">
                <Trophy className="h-12 w-12 mx-auto mb-4 opacity-50" />
                No Analyst Data
              </CardTitle>
            </CardHeader>
            <CardContent className="text-center text-muted-foreground">
              <p>Analyst performance data will appear here once memos are approved and tracked.</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-6">
            {/* Top 3 podium cards */}
            {analysts.length >= 3 && (
              <div className="grid grid-cols-3 gap-4 mb-6">
                {/* Second place */}
                <Card className="border-gray-400/50">
                  <CardContent className="pt-6 text-center">
                    <Medal className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                    <div className="text-sm text-muted-foreground mb-1">2nd Place</div>
                    <div className="flex items-center justify-center gap-2 mb-2">
                      <User className="h-4 w-4" />
                      <span className="font-semibold">{analysts[1].analyst}</span>
                    </div>
                    <div className="text-2xl font-bold text-gray-400">
                      {formatPercent(analysts[1].win_rate)}
                    </div>
                    <div className="text-sm text-muted-foreground">win rate</div>
                  </CardContent>
                </Card>

                {/* First place */}
                <Card className="border-yellow-500/50 bg-yellow-500/5">
                  <CardContent className="pt-6 text-center">
                    <Crown className="h-10 w-10 text-yellow-500 mx-auto mb-2" />
                    <div className="text-sm text-muted-foreground mb-1">1st Place</div>
                    <div className="flex items-center justify-center gap-2 mb-2">
                      <User className="h-4 w-4" />
                      <span className="font-semibold text-lg">{analysts[0].analyst}</span>
                    </div>
                    <div className="text-3xl font-bold text-yellow-500">
                      {formatPercent(analysts[0].win_rate)}
                    </div>
                    <div className="text-sm text-muted-foreground">win rate</div>
                  </CardContent>
                </Card>

                {/* Third place */}
                <Card className="border-amber-600/50">
                  <CardContent className="pt-6 text-center">
                    <Medal className="h-8 w-8 text-amber-600 mx-auto mb-2" />
                    <div className="text-sm text-muted-foreground mb-1">3rd Place</div>
                    <div className="flex items-center justify-center gap-2 mb-2">
                      <User className="h-4 w-4" />
                      <span className="font-semibold">{analysts[2].analyst}</span>
                    </div>
                    <div className="text-2xl font-bold text-amber-600">
                      {formatPercent(analysts[2].win_rate)}
                    </div>
                    <div className="text-sm text-muted-foreground">win rate</div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Full leaderboard table */}
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">Rank</TableHead>
                  <TableHead>Analyst</TableHead>
                  <TableHead className="text-right">Total Ideas</TableHead>
                  <TableHead className="text-right">Approved</TableHead>
                  <TableHead className="text-right">Wins</TableHead>
                  <TableHead className="text-right">
                    <span className={cn(sortBy === 'win_rate' && 'text-primary font-bold')}>
                      Win Rate
                    </span>
                  </TableHead>
                  <TableHead className="text-right">Total Return</TableHead>
                  <TableHead className="text-right">
                    <span className={cn(sortBy === 'avg_return' && 'text-primary font-bold')}>
                      Avg Return
                    </span>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {analysts.map((analyst, index) => (
                  <TableRow key={analyst.analyst}>
                    <TableCell>
                      <div className="flex items-center justify-center">
                        {getRankIcon(index)}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center">
                          <User className="h-4 w-4 text-muted-foreground" />
                        </div>
                        <span className="font-medium">{analyst.analyst}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">{analyst.total_memos}</TableCell>
                    <TableCell className="text-right">
                      <Badge variant="secondary">{analyst.approved_count}</Badge>
                    </TableCell>
                    <TableCell className="text-right">{analyst.win_count}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        {/* Progress bar */}
                        <div className="w-16 h-2 bg-muted rounded-full overflow-hidden">
                          <div
                            className={cn(
                              'h-full rounded-full',
                              analyst.win_rate >= 60 ? 'bg-green-500' :
                              analyst.win_rate >= 40 ? 'bg-yellow-500' : 'bg-red-500'
                            )}
                            style={{ width: `${analyst.win_rate}%` }}
                          />
                        </div>
                        <span className="font-medium">{formatPercent(analyst.win_rate)}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <span className={cn(analyst.total_return >= 0 ? 'text-green-500' : 'text-red-500')}>
                        {formatPercent(analyst.total_return, true)}
                      </span>
                    </TableCell>
                    <TableCell className="text-right">
                      <span
                        className={cn(
                          'flex items-center justify-end gap-1 font-medium',
                          analyst.avg_return >= 0 ? 'text-green-500' : 'text-red-500'
                        )}
                      >
                        {analyst.avg_return >= 0 ? (
                          <ArrowUp className="h-3 w-3" />
                        ) : (
                          <ArrowDown className="h-3 w-3" />
                        )}
                        {formatPercent(Math.abs(analyst.avg_return))}
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>
    </div>
  );
}
