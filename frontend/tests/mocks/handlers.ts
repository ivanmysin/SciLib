import { http, HttpResponse } from 'msw';

const API_BASE = '/api/v1';

export const handlers = [
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
    return HttpResponse.json({ detail: 'Invalid credentials' }, { status: 401 });
  }),
  http.get(`${API_BASE}/users/me`, () => {
    return HttpResponse.json({
      id: 'user-1',
      email: 'test@example.com',
      full_name: 'Test User',
      role: 'user',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    });
  }),
  http.get(`${API_BASE}/items`, () => {
    return HttpResponse.json([{
      id: 'item-1',
      title: 'Test Paper',
      authors: [{ given_name: 'John', family_name: 'Doe' }],
      year: 2024,
      journal: 'Test Journal',
      item_type: 'article',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      attachments: [],
      tags: [],
      collections: [],
    }]);
  }),
  http.get(`${API_BASE}/collections`, () => {
    return HttpResponse.json([{
      id: 'col-1',
      name: 'My Collection',
      item_count: 5,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }]);
  }),
];
