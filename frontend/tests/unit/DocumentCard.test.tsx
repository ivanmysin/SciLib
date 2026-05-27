import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DocumentCard } from '@/components/DocumentCard';
import type { Item } from '@/types/api';

const mockItem: Item = {
  id: '1',
  title: 'Test Paper Title',
  authors: [{ given_name: 'John', family_name: 'Doe', affiliation: 'University' }],
  year: 2023,
  item_type: 'article',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  attachments: [],
  tags: [{ id: '1', name: 'test-tag', item_count: 1 }],
  collections: [],
};

describe('DocumentCard', () => {
  it('renders item title', () => {
    render(<DocumentCard item={mockItem} />);
    expect(screen.getByText('Test Paper Title')).toBeInTheDocument();
  });

  it('renders author name', () => {
    render(<DocumentCard item={mockItem} />);
    expect(screen.getByText(/Doe, John/)).toBeInTheDocument();
  });

  it('renders year when provided', () => {
    render(<DocumentCard item={mockItem} />);
    expect(screen.getByText('2023')).toBeInTheDocument();
  });

  it('renders tag badge', () => {
    render(<DocumentCard item={mockItem} />);
    expect(screen.getByText('test-tag')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const onClick = vi.fn();
    render(<DocumentCard item={mockItem} onClick={onClick} />);
    screen.getByRole('button').click();
    expect(onClick).toHaveBeenCalled();
  });
});
