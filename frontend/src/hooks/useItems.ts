import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/api/client';
import type { Item, CreateItemRequest, UpdateItemRequest } from '@/types/api';

const ITEMS_QUERY_KEY = 'items';

export function useItems(collectionId?: string) {
  return useQuery({
    queryKey: [ITEMS_QUERY_KEY, collectionId],
    queryFn: async () => {
      const params = collectionId ? { collection_id: collectionId } : {};
      const response = await apiClient.get<{ items: Item[] }>('/items', { params });
      return response.data.items;
    },
  });
}

export function useItem(id: string) {
  return useQuery({
    queryKey: [ITEMS_QUERY_KEY, id],
    queryFn: async () => {
      const response = await apiClient.get<Item>(`/items/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useCreateItem() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: CreateItemRequest & { file?: File }) => {
      if (data.file) {
        const formData = new FormData();
        formData.append('file', data.file);
        formData.append('title', data.title);
        formData.append('item_type', data.item_type);
        
        const response = await apiClient.post<Item>('/items/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
      } else {
        const response = await apiClient.post<Item>('/items', data);
        return response.data;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [ITEMS_QUERY_KEY] });
    },
  });
}

export function useUpdateItem(id: string) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: UpdateItemRequest) => {
      const response = await apiClient.patch<Item>(`/items/${id}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [ITEMS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [ITEMS_QUERY_KEY, id] });
    },
  });
}

export function useDeleteItem() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/items/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [ITEMS_QUERY_KEY] });
    },
  });
}
