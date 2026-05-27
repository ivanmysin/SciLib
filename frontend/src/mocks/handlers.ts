import { http, HttpResponse } from 'msw';

const API_BASE = '/api/v1';

export const handlers = [
  // Auth
  http.post(`${API_BASE}/auth/login`, async ({ request }) => {
    const body = await request.json() as { email: string; password: string };
    
    if (body.email === 'test@example.com' && body.password === 'password') {
      return HttpResponse.json({
        access_token: 'mock_access_token',
        refresh_token: 'mock_refresh_token',
        token_type: 'bearer',
        expires_in: 3600,
      });
    }
    
    return HttpResponse.json(
      { detail: 'Invalid credentials' },
      { status: 401 }
    );
  }),

  // Items
  http.get(`${API_BASE}/items`, () => {
    return HttpResponse.json({
      items: [
        {
          id: '1',
          title: 'Deep Learning for Natural Language Processing',
          authors: [{ given_name: 'John', family_name: 'Smith', affiliation: 'MIT' }],
          year: 2023,
          journal: 'Journal of AI Research',
          doi: '10.1234/jair.2023.001',
          abstract: 'This paper presents a comprehensive survey...',
          item_type: 'article' as const,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
          attachments: [],
          tags: [{ id: '1', name: 'deep-learning', color: '#3b82f6', item_count: 5 }],
          collections: [],
        },
      ],
    });
  }),

  // Collections
  http.get(`${API_BASE}/collections`, () => {
    return HttpResponse.json({
      collections: [
        {
          id: '1',
          name: 'Machine Learning',
          parent_id: null,
          children: [],
          item_count: 5,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ],
    });
  }),

  // Search
  http.post(`${API_BASE}/search`, async ({ request }) => {
    const body = await request.json() as { query: string };
    
    return HttpResponse.json({
      items: [],
      total: 0,
      has_more: false,
    });
  }),
];
