// Types for the Human-in-the-Loop Research Platform

export interface Memo {
  id: string;
  ticker: string;
  analyst: string;
  signal: 'bullish' | 'bearish';
  conviction: number;
  thesis: string;
  bull_case: string[];
  bear_case: string[];
  metrics: Record<string, number | string>;
  current_price: number;
  target_price: number;
  time_horizon: 'short' | 'medium' | 'long';
  status: 'pending' | 'approved' | 'rejected';
  generated_at: string;
}

export interface Investment {
  id: string;
  memo_id: string;
  ticker: string;
  analyst: string;
  signal: 'bullish' | 'bearish';
  entry_price: number;
  entry_date: string;
  status: 'active' | 'closed';
  exit_price?: number;
  exit_date?: string;
  current_price?: number;
  pnl_percent?: number;
}

export interface AnalystStats {
  analyst: string;
  total_memos: number;
  approved_count: number;
  win_count: number;
  win_rate: number;
  total_return: number;
  avg_return: number;
}

export interface InboxFilters {
  analyst?: string;
  signal?: 'bullish' | 'bearish';
  minConviction?: number;
}

export interface InvestmentFilters {
  status?: 'active' | 'closed';
  analyst?: string;
}

export type LeaderboardSortBy = 'win_rate' | 'avg_return' | 'total_memos';
