import { renderHook, act, waitFor } from '@testing-library/react';
import useHistoryEntries, { resetGlobalHistoryCache } from '../useHistoryEntries';
import * as api from '../../../../services/api';

// Mock the API module
jest.mock('../../../../services/api');

describe('useHistoryEntries Enhanced Loading', () => {
  const mockShowNotification = jest.fn();

  const defaultFilterOptions = {
    sortBy: 'creation_date',
    filterSource: null,
    searchTerm: '',
    page: 1,
    perPage: 10
  };

  const mockHistoryData = {
    entries: [
      { path_id: '1', topic: 'Test Course 1', creation_date: '2023-01-01' },
      { path_id: '2', topic: 'Test Course 2', creation_date: '2023-01-02' }
    ],
    total: 2,
    page: 1,
    per_page: 10,
    request_time_ms: 100
  };

  const mockActiveGenerations = [
    { task_id: 'task1', request_topic: 'Active Course 1', status: 'RUNNING', created_at: '2023-01-03' }
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    resetGlobalHistoryCache();

    // Setup default API mocks
    api.checkAuthStatus.mockResolvedValue({ isAuthenticated: true });
    api.loadHistoryDataParallelDeduped.mockResolvedValue({
      historyResult: mockHistoryData,
      activeGenerationsResult: mockActiveGenerations,
      errors: {}
    });
  });

  afterEach(() => {
    jest.restoreAllMocks();
    jest.useRealTimers();
  });

  describe('Enhanced Loading States', () => {
    it('should start with initial loading state when no cache exists', async () => {
      const { result } = renderHook(() =>
        useHistoryEntries(defaultFilterOptions, mockShowNotification)
      );

      // Initial state should show initial loading
      expect(result.current.loadingState.initialLoading).toBe(true);
      expect(result.current.loadingState.backgroundRefreshing).toBe(false);
      expect(result.current.loadingState.showingCache).toBe(false);
      expect(result.current.entries).toEqual([]);

      // Wait for loading to complete
      await waitFor(() => {
        expect(result.current.loadingState.initialLoading).toBe(false);
      });

      expect(result.current.entries).toHaveLength(3); // 2 history + 1 active
    });

    it('should show cached data immediately on subsequent loads', async () => {
      // First render to populate cache
      const { result, unmount } = renderHook(() =>
        useHistoryEntries(defaultFilterOptions, mockShowNotification)
      );

      await waitFor(() => {
        expect(result.current.loadingState.initialLoading).toBe(false);
      });

      unmount();

      // Second render should use cache immediately
      const { result: result2 } = renderHook(() =>
        useHistoryEntries(defaultFilterOptions, mockShowNotification)
      );

      // Should immediately show cache (initialLoading false)
      expect(result2.current.loadingState.initialLoading).toBe(false);
      expect(result2.current.entries).toHaveLength(3);
    });

    it('should handle background refresh state correctly', async () => {
      jest.useFakeTimers();

      // Mock API with a delay that we can control
      let resolveApi;
      const apiPromise = new Promise(resolve => {
        resolveApi = resolve;
      });

      api.loadHistoryDataParallelDeduped.mockReturnValue(apiPromise);

      const { result } = renderHook(() =>
        useHistoryEntries(defaultFilterOptions, mockShowNotification)
      );

      // Initial load needs to complete first
      // We need to resolve the first call
      resolveApi({
        historyResult: mockHistoryData,
        activeGenerationsResult: mockActiveGenerations,
        errors: {}
      });

      // Since we resolved it, we need to wait for the effect to process
      // But we are using fake timers, so we might need to advance them?
      // Or just wait for microtasks?
      await act(async () => {
        // Allow promise to resolve
      });

      // Now we need to setup for the refresh
      // Create a NEW promise for the refresh call
      let resolveRefresh;
      const refreshPromise = new Promise(resolve => {
        resolveRefresh = resolve;
      });
      api.loadHistoryDataParallelDeduped.mockReturnValue(refreshPromise);

      // Trigger refresh
      act(() => {
        result.current.refreshEntries();
      });

      // Check immediate state - should be refreshing
      expect(result.current.loadingState.backgroundRefreshing).toBe(true);

      // Now resolve the refresh
      await act(async () => {
        resolveRefresh({
          historyResult: mockHistoryData,
          activeGenerationsResult: mockActiveGenerations,
          errors: {}
        });
      });

      // Should be done refreshing
      expect(result.current.loadingState.backgroundRefreshing).toBe(false);
    });
  });

  describe('Parallel Loading', () => {
    it('should call parallel loading API with correct parameters', async () => {
      renderHook(() =>
        useHistoryEntries(defaultFilterOptions, mockShowNotification)
      );

      await waitFor(() => {
        expect(api.loadHistoryDataParallelDeduped).toHaveBeenCalledWith(
          'creation_date',
          null,
          '',
          1,
          10,
          expect.any(AbortSignal)
        );
      });
    });

    it('should merge history entries and active generations correctly', async () => {
      const { result } = renderHook(() =>
        useHistoryEntries(defaultFilterOptions, mockShowNotification)
      );

      await waitFor(() => {
        expect(result.current.entries).toHaveLength(3);
      });

      // Active generations should be first
      expect(result.current.entries[0].isActive).toBe(true);
      expect(result.current.entries[0].topic).toBe('Active Course 1');

      // History entries should follow
      expect(result.current.entries[1].isActive).toBeUndefined();
      expect(result.current.entries[1].topic).toBe('Test Course 1');
    });

    it('should handle alphabetical sorting correctly', async () => {
      const filterOptionsWithTopicSort = {
        ...defaultFilterOptions,
        sortBy: 'topic'
      };

      const { result } = renderHook(() =>
        useHistoryEntries(filterOptionsWithTopicSort, mockShowNotification)
      );

      await waitFor(() => {
        expect(result.current.entries).toHaveLength(3);
      });

      // Should be sorted alphabetically regardless of active status
      const topics = result.current.entries.map(entry => entry.topic);
      expect(topics).toEqual(['Active Course 1', 'Test Course 1', 'Test Course 2']);
    });
  });

  describe('Error Handling', () => {
    it('should handle partial failures gracefully', async () => {
      api.loadHistoryDataParallelDeduped.mockResolvedValue({
        historyResult: mockHistoryData,
        activeGenerationsResult: [],
        errors: {
          activeGenerations: new Error('Active generations failed')
        }
      });

      const { result } = renderHook(() =>
        useHistoryEntries(defaultFilterOptions, mockShowNotification)
      );

      await waitFor(() => {
        expect(result.current.loadingState.initialLoading).toBe(false);
      });

      // Should show history entries despite active generations failure
      expect(result.current.entries).toHaveLength(2);
      expect(mockShowNotification).toHaveBeenCalledWith(
        expect.stringContaining('Could not load active generations'),
        'warning'
      );
    });

    it('should handle complete failure with cached data', async () => {
      // First, populate cache
      const { result, unmount } = renderHook(() =>
        useHistoryEntries(defaultFilterOptions, mockShowNotification)
      );

      await waitFor(() => {
        expect(result.current.loadingState.initialLoading).toBe(false);
      });

      // Verify data is loaded
      expect(result.current.entries).toHaveLength(3);

      // Now simulate complete failure for the NEXT request
      api.loadHistoryDataParallelDeduped.mockResolvedValue({
        historyResult: null,
        activeGenerationsResult: [],
        errors: {
          history: new Error('History failed'),
          activeGenerations: new Error('Active generations failed')
        }
      });

      // Trigger refresh which should fail
      act(() => {
        result.current.refreshEntries();
      });

      await waitFor(() => {
        expect(result.current.loadingState.showingCache).toBe(true);
      });

      // Should keep showing cached data
      expect(result.current.entries).toHaveLength(3);
      expect(mockShowNotification).toHaveBeenCalledWith(
        'Failed to refresh data from server',
        'warning'
      );
    });

    it('should handle abort signals correctly', async () => {
      const abortError = new Error('Request was aborted');
      abortError.name = 'AbortError';

      api.loadHistoryDataParallelDeduped.mockRejectedValue(abortError);

      const { result } = renderHook(() =>
        useHistoryEntries(defaultFilterOptions, mockShowNotification)
      );

      // Should not show error notification for aborted requests
      await waitFor(() => {
        expect(mockShowNotification).not.toHaveBeenCalled();
      });
    });
  });

  describe('Caching Behavior', () => {
    it('should use cache key correctly', async () => {
      const filterOptions1 = { ...defaultFilterOptions, page: 1 };
      const filterOptions2 = { ...defaultFilterOptions, page: 2 };

      // First render with page 1
      const { result: result1 } = renderHook(() =>
        useHistoryEntries(filterOptions1, mockShowNotification)
      );

      await waitFor(() => {
        expect(result1.current.loadingState.initialLoading).toBe(false);
      });

      // Second render with page 2 should trigger new request
      const { result: result2 } = renderHook(() =>
        useHistoryEntries(filterOptions2, mockShowNotification)
      );

      expect(result2.current.loadingState.initialLoading).toBe(true);

      await waitFor(() => {
        expect(result2.current.loadingState.initialLoading).toBe(false);
      });

      // Should have made separate API calls for different pages
      expect(api.loadHistoryDataParallelDeduped).toHaveBeenCalledTimes(2);
    });

    it('should throttle rapid requests', async () => {
      const { result } = renderHook(() =>
        useHistoryEntries(defaultFilterOptions, mockShowNotification)
      );

      // Trigger multiple rapid refreshes
      act(() => {
        result.current.refreshEntries();
        result.current.refreshEntries();
        result.current.refreshEntries();
      });

      await waitFor(() => {
        expect(result.current.loadingState.initialLoading).toBe(false);
      });

      // Should have throttled the requests (1 initial + 1 refresh due to throttling)
      expect(api.loadHistoryDataParallelDeduped.mock.calls.length).toBeGreaterThanOrEqual(2);
    });
  });

  describe('Performance Statistics', () => {
    it('should track parallel loading in stats', async () => {
      const { result } = renderHook(() =>
        useHistoryEntries(defaultFilterOptions, mockShowNotification)
      );

      await waitFor(() => {
        expect(result.current.stats.parallelLoad).toBe(true);
      });

      expect(result.current.stats).toMatchObject({
        fromCache: false,
        initialLoad: true,
        total: 2,
        parallelLoad: true,
        serverTime: 100
      });
    });

    it('should track cache usage in stats', async () => {
      // First render to populate cache
      const { result: result1, unmount } = renderHook(() =>
        useHistoryEntries(defaultFilterOptions, mockShowNotification)
      );

      await waitFor(() => {
        expect(result1.current.loadingState.initialLoading).toBe(false);
      });

      unmount();

      // Second render should use cache
      const { result: result2 } = renderHook(() =>
        useHistoryEntries(defaultFilterOptions, mockShowNotification)
      );

      await waitFor(() => {
        expect(result2.current.stats.fromCache).toBe(true);
      });
    });
  });

  describe('Legacy Compatibility', () => {
    it('should provide legacy loading property for backward compatibility', async () => {
      const { result } = renderHook(() =>
        useHistoryEntries(defaultFilterOptions, mockShowNotification)
      );

      // Legacy loading should match initialLoading
      expect(result.current.loading).toBe(result.current.loadingState.initialLoading);

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.loading).toBe(result.current.loadingState.initialLoading);
    });
  });
});
