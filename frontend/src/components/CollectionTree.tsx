import React, { useState } from 'react';
import { ChevronRight, ChevronDown, Folder, FolderOpen } from 'lucide-react';
import type { Collection } from '@/types/api';

interface CollectionTreeNodeProps {
  collection: Collection;
  level: number;
  selectedId?: string;
  onSelect: (id: string) => void;
  onExpand: (id: string) => void;
  expandedIds: Set<string>;
}

function CollectionTreeNode({ 
  collection, 
  level, 
  selectedId, 
  onSelect,
  onExpand,
  expandedIds 
}: CollectionTreeNodeProps) {
  const isExpanded = expandedIds.has(collection.id);
  const isSelected = selectedId === collection.id;
  const hasChildren = collection.children && collection.children.length > 0;

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (hasChildren) {
      onExpand(collection.id);
    }
  };

  const handleClick = () => {
    onSelect(collection.id);
  };

  return (
    <div>
      <div
        className={`flex items-center gap-2 px-2 py-1.5 rounded-md cursor-pointer transition-colors ${
          isSelected 
            ? 'bg-primary text-primary-foreground' 
            : 'hover:bg-muted'
        }`}
        style={{ paddingLeft: `${level * 12 + 8}px` }}
        onClick={handleClick}
      >
        <button
          onClick={handleToggle}
          className="p-0.5 hover:bg-background/50 rounded"
          disabled={!hasChildren}
        >
          {hasChildren ? (
            isExpanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )
          ) : (
            <span className="w-4" />
          )}
        </button>
        {isExpanded ? (
          <FolderOpen className="h-4 w-4" />
        ) : (
          <Folder className="h-4 w-4" />
        )}
        <span className="text-sm font-medium truncate flex-1">
          {collection.name}
        </span>
        <span className={`text-xs ${isSelected ? 'text-primary-foreground/70' : 'text-muted-foreground'}`}>
          {collection.item_count}
        </span>
      </div>
      {isExpanded && collection.children && (
        <div>
          {collection.children.map((child) => (
            <CollectionTreeNode
              key={child.id}
              collection={child}
              level={level + 1}
              selectedId={selectedId}
              onSelect={onSelect}
              onExpand={onExpand}
              expandedIds={expandedIds}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface CollectionTreeProps {
  collections: Collection[];
  selectedId?: string;
  onSelect: (id: string) => void;
}

export function CollectionTree({ collections, selectedId, onSelect }: CollectionTreeProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  const handleExpand = (id: string) => {
    setExpandedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  return (
    <div className="py-2">
      {collections.map((collection) => (
        <CollectionTreeNode
          key={collection.id}
          collection={collection}
          level={0}
          selectedId={selectedId}
          onSelect={onSelect}
          onExpand={handleExpand}
          expandedIds={expandedIds}
        />
      ))}
    </div>
  );
}
