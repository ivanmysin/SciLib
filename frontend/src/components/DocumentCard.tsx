import React from 'react';
import { FileText, Calendar, Users, Tag } from 'lucide-react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Item } from '@/types/api';

interface DocumentCardProps {
  item: Item;
  onClick?: () => void;
  onContextMenu?: (e: React.MouseEvent) => void;
}

export function DocumentCard({ item, onClick, onContextMenu }: DocumentCardProps) {
  const primaryAuthor = item.authors[0];
  const authorText = primaryAuthor
    ? `${primaryAuthor.family_name}, ${primaryAuthor.given_name}`
    : 'Unknown Author';

  const shortTitle = item.title.length > 80 
    ? item.title.substring(0, 80) + '...' 
    : item.title;

  return (
    <Card 
      className="cursor-pointer transition-all hover:shadow-md hover:border-primary/50"
      onClick={onClick}
      onContextMenu={onContextMenu}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick?.();
        }
      }}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
            <FileText className="h-5 w-5 text-primary" />
          </div>
          <div className="flex-1 overflow-hidden">
            <h3 className="font-semibold leading-tight line-clamp-2" title={item.title}>
              {shortTitle}
            </h3>
            <p className="text-sm text-muted-foreground mt-1">
              {authorText}
              {item.year && ` (${item.year})`}
            </p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="flex flex-wrap gap-1 mt-2">
          <Badge variant="secondary" className="text-xs">
            {item.item_type}
          </Badge>
          {item.tags.slice(0, 3).map((tag) => (
            <Badge key={tag.id} variant="outline" className="text-xs">
              <Tag className="h-3 w-3 mr-1" />
              {tag.name}
            </Badge>
          ))}
          {item.tags.length > 3 && (
            <Badge variant="outline" className="text-xs">
              +{item.tags.length - 3}
            </Badge>
          )}
        </div>
        {item.abstract && (
          <p className="text-xs text-muted-foreground mt-2 line-clamp-2">
            {item.abstract}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
