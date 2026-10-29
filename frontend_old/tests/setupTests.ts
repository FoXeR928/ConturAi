import '@testing-library/jest-dom';
import { afterEach, beforeEach, vi } from 'vitest';

// jsdom не реализует scrollIntoView
Element.prototype.scrollIntoView = vi.fn();

// Стабильный location — чтобы 401-редирект не падал с "Not implemented: navigation"
const ORIGINAL_LOCATION = window.location;

export function mockLocation(pathname = '/chat') {
  Object.defineProperty(window, 'location', {
    configurable: true,
    writable: true,
    value: {
      pathname,
      get href() {
        return `http://localhost${pathname}`;
      },
      set href(_v: string) {
        /* no-op — иначе jsdom кидает navigation error */
      },
    },
  });
}

beforeEach(() => {
  localStorage.clear();
  mockLocation('/chat');
});

afterEach(() => {
  Object.defineProperty(window, 'location', {
    configurable: true,
    writable: true,
    value: ORIGINAL_LOCATION,
  });
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});