import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { Memo } from '@/types/research';
import {
  ArrowDown,
  ArrowUp,
  ChevronDown,
  ChevronUp,
  Clock,
  Target,
  TrendingDown,
  TrendingUp,
  User,
} from 'lucide-react';
import { useState } from 'react';

interface MemoCardProps {
  memo: Memo;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
  isLoading?: boolean;
}

export function MemoCard({ memo, onApprove, onReject, isLoading = false }: MemoCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const isBullish = memo.signal === 'bullish';
  const SignalIcon = isBullish ? TrendingUp : TrendingDown;
  const signalColor = isBullish ? 'text-green-500' : 'text-red-500';
  const signalBgColor = isBullish ? 'bg-green-500/10' : 'bg-red-500/10';

  const timeHorizonLabels: Record<string, string> = {
    short: '< 3 months',
    medium: '3-12 months',
    long: '> 12 months',
  };

  const priceChange = ((memo.target_price - memo.current_price) / memo.current_price) * 100;

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(price);
  };

  const formatMetricValue = (value: number | string) => {
    if (typeof value === 'number') {
      if (Math.abs(value) >= 1e9) {
        return `${(value / 1e9).toFixed(2)}B`;
      }
      if (Math.abs(value) >= 1e6) {
        return `${(value / 1e6).toFixed(2)}M`;
      }
      if (Math.abs(value) < 1) {
        return value.toFixed(4);
      }
      return value.toFixed(2);
    }
    return value;
  };

  return (
    <Card
      className={cn(
        'transition-all duration-200 hover:shadow-md cursor-pointer',
        isExpanded && 'ring-2 ring-primary/20'
      )}
    >
      <CardHeader
        className="pb-2"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            {/* Signal indicator */}
            <div className={cn('p-2 rounded-lg', signalBgColor)}>
              <SignalIcon className={cn('h-5 w-5', signalColor)} />
            </div>

            {/* Ticker and analyst */}
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold">{memo.ticker}</h3>
                <Badge
                  variant={isBullish ? 'success' : 'destructive'}
                  className="text-xs"
                >
                  {memo.signal.toUpperCase()}
                </Badge>
              </div>
              <div className="flex items-center gap-1 text-sm text-muted-foreground">
                <User className="h-3 w-3" />
                <span>{memo.analyst}</span>
              </div>
            </div>
          </div>

          {/* Conviction and expand toggle */}
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-sm text-muted-foreground">Conviction</div>
              <div className={cn('text-xl font-bold', memo.conviction >= 70 ? 'text-green-500' : memo.conviction >= 50 ? 'text-yellow-500' : 'text-red-500')}>
                {memo.conviction}%
              </div>
            </div>
            {isExpanded ? (
              <ChevronUp className="h-5 w-5 text-muted-foreground" />
            ) : (
              <ChevronDown className="h-5 w-5 text-muted-foreground" />
            )}
          </div>
        </div>

        {/* Thesis preview (always visible) */}
        <p className={cn('mt-3 text-sm text-muted-foreground', !isExpanded && 'line-clamp-2')}>
          {memo.thesis}
        </p>
      </CardHeader>

      {isExpanded && (
        <CardContent className="pt-0 space-y-4">
          {/* Price info */}
          <div className="grid grid-cols-3 gap-4 p-3 bg-muted/50 rounded-lg">
            <div>
              <div className="text-xs text-muted-foreground">Current Price</div>
              <div className="font-semibold">{formatPrice(memo.current_price)}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Target Price</div>
              <div className={cn('font-semibold', isBullish ? 'text-green-500' : 'text-red-500')}>
                {formatPrice(memo.target_price)}
              </div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Expected Move</div>
              <div className={cn('font-semibold flex items-center gap-1', priceChange >= 0 ? 'text-green-500' : 'text-red-500')}>
                {priceChange >= 0 ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />}
                {Math.abs(priceChange).toFixed(1)}%
              </div>
            </div>
          </div>

          {/* Time horizon */}
          <div className="flex items-center gap-2 text-sm">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">Time Horizon:</span>
            <Badge variant="outline">{timeHorizonLabels[memo.time_horizon]}</Badge>
          </div>

          {/* Bull case */}
          {memo.bull_case && memo.bull_case.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Target className="h-4 w-4 text-green-500" />
                <h4 className="font-semibold text-green-500">Bull Case</h4>
              </div>
              <ul className="space-y-1 ml-6">
                {memo.bull_case.map((point, index) => (
                  <li key={index} className="text-sm text-muted-foreground list-disc">
                    {point}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Bear case */}
          {memo.bear_case && memo.bear_case.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Target className="h-4 w-4 text-red-500" />
                <h4 className="font-semibold text-red-500">Bear Case</h4>
              </div>
              <ul className="space-y-1 ml-6">
                {memo.bear_case.map((point, index) => (
                  <li key={index} className="text-sm text-muted-foreground list-disc">
                    {point}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Key metrics table */}
          {memo.metrics && Object.keys(memo.metrics).length > 0 && (
            <div>
              <h4 className="font-semibold mb-2">Key Metrics</h4>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {Object.entries(memo.metrics).map(([key, value]) => (
                  <div key={key} className="p-2 bg-muted/50 rounded-md">
                    <div className="text-xs text-muted-foreground capitalize">
                      {key.replace(/_/g, ' ')}
                    </div>
                    <div className="font-medium">{formatMetricValue(value)}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Catalysts */}
          {memo.catalysts && (memo.catalysts.next_earnings || memo.catalysts.ex_dividend_date) && (
            <div>
              <h4 className="font-semibold mb-2">Upcoming Catalysts</h4>
              <div className="grid grid-cols-2 gap-2">
                {memo.catalysts.next_earnings && (
                  <div className="p-2 bg-blue-500/10 rounded-md">
                    <div className="text-xs text-muted-foreground">Next Earnings</div>
                    <div className="font-medium">{memo.catalysts.next_earnings}</div>
                    {memo.catalysts.days_to_earnings !== null && (
                      <div className="text-xs text-blue-500">{memo.catalysts.days_to_earnings} days</div>
                    )}
                  </div>
                )}
                {memo.catalysts.ex_dividend_date && (
                  <div className="p-2 bg-green-500/10 rounded-md">
                    <div className="text-xs text-muted-foreground">Ex-Dividend</div>
                    <div className="font-medium">{memo.catalysts.ex_dividend_date}</div>
                    {memo.catalysts.dividend_yield && (
                      <div className="text-xs text-green-500">{memo.catalysts.dividend_yield}% yield</div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Position Sizing */}
          {memo.position_sizing && memo.position_sizing.recommended_pct && (
            <div>
              <h4 className="font-semibold mb-2">Position Sizing</h4>
              <div className="grid grid-cols-3 gap-2">
                <div className="p-2 bg-muted/50 rounded-md">
                  <div className="text-xs text-muted-foreground">Recommended</div>
                  <div className="font-medium">{memo.position_sizing.recommended_pct}%</div>
                </div>
                <div className="p-2 bg-muted/50 rounded-md">
                  <div className="text-xs text-muted-foreground">Max Risk</div>
                  <div className="font-medium">{memo.position_sizing.max_risk_pct}%</div>
                </div>
                <div className="p-2 bg-muted/50 rounded-md">
                  <div className="text-xs text-muted-foreground">Volatility</div>
                  <div className="font-medium">{memo.position_sizing.volatility_annual}%</div>
                </div>
              </div>
              {memo.position_sizing.sizing_rationale && (
                <div className="text-xs text-muted-foreground mt-2">{memo.position_sizing.sizing_rationale}</div>
              )}
            </div>
          )}

          {/* Macro Context */}
          {memo.macro_context && memo.macro_context.vix && (
            <div>
              <h4 className="font-semibold mb-2">Market Context</h4>
              <div className="grid grid-cols-3 gap-2">
                <div className="p-2 bg-muted/50 rounded-md">
                  <div className="text-xs text-muted-foreground">VIX</div>
                  <div className={cn('font-medium', memo.macro_context.vix > 25 ? 'text-red-500' : memo.macro_context.vix < 15 ? 'text-green-500' : '')}>
                    {memo.macro_context.vix}
                  </div>
                  <div className="text-xs text-muted-foreground">{memo.macro_context.vix_level}</div>
                </div>
                <div className="p-2 bg-muted/50 rounded-md">
                  <div className="text-xs text-muted-foreground">10Y Treasury</div>
                  <div className="font-medium">{memo.macro_context.treasury_10y}%</div>
                </div>
                <div className="p-2 bg-muted/50 rounded-md">
                  <div className="text-xs text-muted-foreground">Market Regime</div>
                  <div className={cn('font-medium capitalize',
                    memo.macro_context.market_regime === 'risk-on' ? 'text-green-500' :
                    memo.macro_context.market_regime === 'risk-off' ? 'text-red-500' : '')}>
                    {memo.macro_context.market_regime}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Generated timestamp */}
          <div className="text-xs text-muted-foreground">
            Generated: {new Date(memo.generated_at).toLocaleString()}
          </div>

          {/* Action buttons */}
          <div className="flex gap-3 pt-2">
            <Button
              variant="outline"
              className="flex-1 border-red-500/50 text-red-500 hover:bg-red-500/10 hover:text-red-500"
              onClick={(e) => {
                e.stopPropagation();
                onReject(memo.id);
              }}
              disabled={isLoading}
            >
              Reject
            </Button>
            <Button
              className="flex-1 bg-green-500 hover:bg-green-600 text-white"
              onClick={(e) => {
                e.stopPropagation();
                onApprove(memo.id);
              }}
              disabled={isLoading}
            >
              Approve
            </Button>
          </div>
        </CardContent>
      )}

      {/* Compact action buttons when collapsed */}
      {!isExpanded && (
        <CardContent className="pt-0">
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              className="flex-1 border-red-500/50 text-red-500 hover:bg-red-500/10 hover:text-red-500"
              onClick={(e) => {
                e.stopPropagation();
                onReject(memo.id);
              }}
              disabled={isLoading}
            >
              Reject
            </Button>
            <Button
              size="sm"
              className="flex-1 bg-green-500 hover:bg-green-600 text-white"
              onClick={(e) => {
                e.stopPropagation();
                onApprove(memo.id);
              }}
              disabled={isLoading}
            >
              Approve
            </Button>
          </div>
        </CardContent>
      )}
    </Card>
  );
}
