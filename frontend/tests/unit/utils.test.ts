import { describe, it, expect } from 'vitest';
import { formatDate, formatFileSize, truncate, isValidEmail, isValidDOI } from '@/lib/utils';

describe('utils', () => {
  describe('formatDate', () => {
    it('formats date correctly', () => {
      const result = formatDate('2024-01-15T00:00:00Z');
      expect(result).toMatch(/Jan 15,? 2024/);
    });
  });

  describe('formatFileSize', () => {
    it('formats bytes', () => {
      expect(formatFileSize(0)).toBe('0 B');
      expect(formatFileSize(1024)).toBe('1 KB');
      expect(formatFileSize(1048576)).toBe('1 MB');
    });
  });

  describe('truncate', () => {
    it('truncates long strings', () => {
      expect(truncate('Hello World', 5)).toBe('He...');
    });

    it('does not truncate short strings', () => {
      expect(truncate('Hi', 5)).toBe('Hi');
    });
  });

  describe('isValidEmail', () => {
    it('validates correct emails', () => {
      expect(isValidEmail('test@example.com')).toBe(true);
    });

    it('rejects invalid emails', () => {
      expect(isValidEmail('invalid')).toBe(false);
    });
  });

  describe('isValidDOI', () => {
    it('validates correct DOIs', () => {
      expect(isValidDOI('10.1000/journal.123')).toBe(true);
    });

    it('rejects invalid DOIs', () => {
      expect(isValidDOI('not-a-doi')).toBe(false);
    });
  });
});
