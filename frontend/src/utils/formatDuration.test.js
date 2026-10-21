import { describe, expect, it } from 'vitest';
import { formatDuration } from './formatDuration';

describe('formatDuration', () => {
  it('formats session durations as hours, minutes, and seconds', () => {
    expect(formatDuration(3661)).toBe('01:01:01');
  });

  it('clamps negative durations to zero', () => {
    expect(formatDuration(-1)).toBe('00:00:00');
  });

  it('shows a loading label when the duration is unavailable', () => {
    expect(formatDuration(null)).toBe('Loading...');
  });
});
