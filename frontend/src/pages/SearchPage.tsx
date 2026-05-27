import React, { useState } from 'react';
import { Search, Filter, SlidersHorizontal } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { DocumentCard } from '@/components/DocumentCard';
import { useSearch } from '@/hooks/useSearch';
import type { SearchQuery } from '@/types/api';

export function SearchPage() {
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState<'simple' | 'advanced' | 'semantic'>('simple');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [filters, setFilters] = useState({
    year_from: '',
    year_to: '',
    item_type: '',
  });

  const searchQuery: SearchQuery | null = query.trim() 
    ? {
        query: query.trim(),
        mode,
        filters: showAdvanced ? {
          year_from: filters.year_from ? parseInt(filters.year_from) : undefined,
          year_to: filters.year_to ? parseInt(filters.year_to) : undefined,
          item_types: filters.item_type ? [filters.item_type] : undefined,
        } : undefined,
        limit: 20,
      }
    : null;

  const { data, isLoading, error } = useSearch(searchQuery);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Search</h1>
        <Select value={mode} onValueChange={(v) => setMode(v as typeof mode)}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Search mode" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="simple">Simple Search</SelectItem>
            <SelectItem value="advanced">Advanced Search</SelectItem>
            <SelectItem value="semantic">Semantic Search</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <form onSubmit={handleSearch} className="space-y-4">
        <div className="flex gap-2">
          <Input
            type="text"
            placeholder={mode === 'semantic' ? "Ask a question about research..." : "Search by title, author, DOI..."}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1"
          />
          <Button type="submit">
            <Search className="h-4 w-4 mr-2" />
            Search
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => setShowAdvanced(!showAdvanced)}
          >
            {showAdvanced ? (
              <SlidersHorizontal className="h-4 w-4 mr-2" />
            ) : (
              <Filter className="h-4 w-4 mr-2" />
            )}
            Filters
          </Button>
        </div>

        {showAdvanced && (
          <Card>
            <CardContent className="pt-4 grid grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium mb-1 block">Year from</label>
                <Input
                  type="number"
                  placeholder="From"
                  value={filters.year_from}
                  onChange={(e) => setFilters(f => ({ ...f, year_from: e.target.value }))}
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-1 block">Year to</label>
                <Input
                  type="number"
                  placeholder="To"
                  value={filters.year_to}
                  onChange={(e) => setFilters(f => ({ ...f, year_to: e.target.value }))}
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-1 block">Type</label>
                <Select value={filters.item_type} onValueChange={(v) => setFilters(f => ({ ...f, item_type: v }))}>
                  <SelectTrigger>
                    <SelectValue placeholder="Any type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Any type</SelectItem>
                    <SelectItem value="article">Article</SelectItem>
                    <SelectItem value="book">Book</SelectItem>
                    <SelectItem value="thesis">Thesis</SelectItem>
                    <SelectItem value="report">Report</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
        )}
      </form>

      {isLoading && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardContent className="pt-6">
                <div className="animate-pulse space-y-3">
                  <div className="h-4 bg-muted rounded w-3/4"></div>
                  <div className="h-3 bg-muted rounded w-1/2"></div>
                  <div className="h-3 bg-muted rounded w-full"></div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {error && (
        <div className="text-destructive text-center py-8">
          Error loading results. Please try again.
        </div>
      )}

      {!isLoading && !error && data && data.items.length === 0 && query && (
        <div className="text-muted-foreground text-center py-8">
          No results found for "{query}"
        </div>
      )}

      {!isLoading && !error && data && data.items.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-muted-foreground">
              Found {data.total} results
            </p>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {data.items.map((item) => (
              <DocumentCard key={item.id} item={item} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
