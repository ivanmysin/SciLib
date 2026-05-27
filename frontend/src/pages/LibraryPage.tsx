import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import apiClient from '@/api/client';
import type { Item, Collection } from '@/types/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export function LibraryPage() {
  const [searchQuery, setSearchQuery] = useState('');
  
  const { data: items, isLoading } = useQuery({
    queryKey: ['items'],
    queryFn: async () => {
      const response = await apiClient.get<Item[]>('/items');
      return response.data;
    },
  });

  const { data: collections } = useQuery({
    queryKey: ['collections'],
    queryFn: async () => {
      const response = await apiClient.get<Collection[]>('/collections');
      return response.data;
    },
  });

  const filteredItems = items?.filter(item =>
    item.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (isLoading) {
    return <div className="p-4">Loading...</div>;
  }

  return (
    <div className="flex h-screen">
      {/* Sidebar - Collections */}
      <aside className="w-64 border-r p-4">
        <h2 className="text-lg font-semibold mb-4">Collections</h2>
        <div className="space-y-2">
          {collections?.map((collection) => (
            <div key={collection.id} className="p-2 hover:bg-accent rounded-md cursor-pointer">
              {collection.name} ({collection.item_count})
            </div>
          ))}
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-6 overflow-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">Library</h1>
          <Button>Upload PDF</Button>
        </div>

        <Input
          placeholder="Search library..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="mb-4"
        />

        <div className="grid gap-4">
          {filteredItems?.map((item) => (
            <Card key={item.id}>
              <CardContent className="p-4">
                <h3 className="font-semibold">{item.title}</h3>
                <p className="text-sm text-muted-foreground">
                  {item.authors.map(a => `${a.given_name} ${a.family_name}`).join(', ')}
                  {item.year ? ` • ${item.year}` : ''}
                </p>
                <div className="flex gap-2 mt-2">
                  {item.tags.map(tag => (
                    <span key={tag.id} className="px-2 py-1 bg-secondary text-xs rounded-full">
                      {tag.name}
                    </span>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {filteredItems?.length === 0 && (
          <div className="text-center py-12 text-muted-foreground">
            No items found. Upload your first PDF to get started.
          </div>
        )}
      </main>
    </div>
  );
}
