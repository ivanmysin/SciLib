import { describe, it, expect, beforeEach } from 'vitest';
import { useAuthStore } from '@/store/authStore';

describe('authStore', () => {
  beforeEach(() => {
    localStorage.clear();
    useAuthStore.getState().logout();
  });

  it('initializes with null user', () => {
    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });

  it('sets user on login', () => {
    const mockUser = {
      id: '1',
      email: 'test@example.com',
      full_name: 'Test User',
      role: 'user' as const,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };
    
    useAuthStore.getState().login({
      access_token: 'token',
      refresh_token: 'refresh',
      token_type: 'bearer',
      expires_in: 3600,
    }, mockUser);

    const state = useAuthStore.getState();
    expect(state.user).toEqual(mockUser);
    expect(state.isAuthenticated).toBe(true);
    expect(localStorage.getItem('access_token')).toBe('token');
  });

  it('clears user on logout', () => {
    useAuthStore.getState().login({
      access_token: 'token',
      refresh_token: 'refresh',
      token_type: 'bearer',
      expires_in: 3600,
    }, {
      id: '1',
      email: 'test@example.com',
      full_name: 'Test User',
      role: 'user',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    });

    useAuthStore.getState().logout();

    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });
});
