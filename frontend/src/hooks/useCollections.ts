import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/api/client';
import type { Collection, CreateCollectionRequest } from '@/types/api';

const COLLECTIONS_QUERY_KEY = 'collections';

export function useCollections() {
  return useQuery({
    queryKey: [COLLECTIONS_QUERY_KEY],
    queryFn: async () => {
      const response = await apiClient.get<{ collections: Collection[] }>('/collections');
      return response.data.collections;
    },
  });
}

export function useCreateCollection() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: CreateCollectionRequest) => {
      const response = await apiClient.post<Collection>('/collections', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [COLLECTIONS_QUERY_KEY] });
    },
  });
}

export function useUpdateCollection(id: string) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: Partial<CreateCollectionRequest>) => {
      const response = await apiClient.patch<Collection>(`/collections/${id}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [COLLECTIONS_QUERY_KEY] });
    },
  });
}

export function useDeleteCollection() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/collections/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [COLLECTIONS_QUERY_KEY] });
    },
  });
}
