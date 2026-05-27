import { useQuery } from '@tanstack/react-query';
import apiClient from '@/api/client';
import type { SearchQuery, SearchResult } from '@/types/api';

export function useSearch(query: SearchQuery | null) {
  return useQuery({
    queryKey: ['search', query],
    queryFn: async () => {
      if (!query) return { items: [], total: 0, has_more: false };
      
      const response = await apiClient.post<SearchResult>('/search', query);
      return response.data;
    },
    enabled: !!query,
  });
}
