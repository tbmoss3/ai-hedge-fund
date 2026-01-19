import {
  AnalystStats,
  InboxFilters,
  Investment,
  InvestmentFilters,
  LeaderboardSortBy,
  Memo,
} from '@/types/research';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Research Platform API Service
 * Handles all API calls for the human-in-the-loop research review system
 */
export const researchApi = {
  /**
   * Fetches pending memos from the inbox
   * @param filters Optional filters for analyst, signal, and minimum conviction
   * @returns Promise resolving to array of Memo objects
   */
  getInbox: async (filters?: InboxFilters): Promise<Memo[]> => {
    try {
      const params = new URLSearchParams();
      if (filters?.analyst) params.append('analyst', filters.analyst);
      if (filters?.signal) params.append('signal', filters.signal);
      if (filters?.minConviction !== undefined) {
        params.append('min_conviction', filters.minConviction.toString());
      }

      const queryString = params.toString();
      const url = `${API_BASE_URL}/api/inbox${queryString ? `?${queryString}` : ''}`;

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data.memos || data;
    } catch (error) {
      console.error('Failed to fetch inbox:', error);
      throw error;
    }
  },

  /**
   * Approves a memo and creates an investment
   * @param id The memo ID to approve
   * @returns Promise resolving to the created Investment
   */
  approveMemo: async (id: string): Promise<Investment> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/inbox/${id}/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Failed to approve memo:', error);
      throw error;
    }
  },

  /**
   * Rejects a memo
   * @param id The memo ID to reject
   */
  rejectMemo: async (id: string): Promise<void> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/inbox/${id}/reject`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('Failed to reject memo:', error);
      throw error;
    }
  },

  /**
   * Fetches investments from the portfolio
   * @param filters Optional filters for status and analyst
   * @returns Promise resolving to array of Investment objects
   */
  getInvestments: async (filters?: InvestmentFilters): Promise<Investment[]> => {
    try {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.analyst) params.append('analyst', filters.analyst);

      const queryString = params.toString();
      const url = `${API_BASE_URL}/api/investments${queryString ? `?${queryString}` : ''}`;

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data.investments || data;
    } catch (error) {
      console.error('Failed to fetch investments:', error);
      throw error;
    }
  },

  /**
   * Closes an investment position
   * @param id The investment ID to close
   * @param exitPrice The exit price for the position
   * @returns Promise resolving to the updated Investment
   */
  closeInvestment: async (id: string, exitPrice: number): Promise<Investment> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/investments/${id}/close`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ exit_price: exitPrice }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Failed to close investment:', error);
      throw error;
    }
  },

  /**
   * Fetches analyst leaderboard data
   * @param sortBy Optional sort field
   * @returns Promise resolving to array of AnalystStats objects
   */
  getLeaderboard: async (sortBy?: LeaderboardSortBy): Promise<AnalystStats[]> => {
    try {
      const params = new URLSearchParams();
      if (sortBy) params.append('sort_by', sortBy);

      const queryString = params.toString();
      const url = `${API_BASE_URL}/api/analysts/leaderboard${queryString ? `?${queryString}` : ''}`;

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data.analysts || data;
    } catch (error) {
      console.error('Failed to fetch leaderboard:', error);
      throw error;
    }
  },

  /**
   * Fetches a single memo by ID
   * @param id The memo ID
   * @returns Promise resolving to the Memo object
   */
  getMemo: async (id: string): Promise<Memo> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/inbox/${id}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch memo:', error);
      throw error;
    }
  },

  /**
   * Gets the count of pending memos in the inbox
   * @returns Promise resolving to the count number
   */
  getInboxCount: async (): Promise<number> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/inbox/count`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data.count;
    } catch (error) {
      console.error('Failed to fetch inbox count:', error);
      throw error;
    }
  },

  /**
   * Gets list of unique analysts for filtering
   * @returns Promise resolving to array of analyst names
   */
  getAnalysts: async (): Promise<string[]> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/analysts`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data.analysts || data;
    } catch (error) {
      console.error('Failed to fetch analysts:', error);
      throw error;
    }
  },
};
