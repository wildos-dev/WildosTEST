import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock environment variables
vi.mock('import.meta.env', () => ({
  VITE_API_BASE_URL: 'http://localhost:8000',
  VITE_DASHBOARD_PATH: '/dashboard',
  MODE: 'test',
  DEV: false,
  PROD: false,
  SSR: false
}))

// Mock react-router
vi.mock('wouter', () => ({
  useLocation: () => ['/dashboard', vi.fn()],
  useRoute: () => [true, {}],
  Link: ({ children, ...props }: any) => <a {...props}>{children}</a>,
  Router: ({ children }: any) => children,
  Route: ({ children }: any) => children
}))

// Mock i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: {
      changeLanguage: () => new Promise(() => {}),
      language: 'en'
    }
  }),
  initReactI18next: {
    type: '3rdParty',
    init: () => {}
  }
}))

// Mock fetch for API calls
global.fetch = vi.fn()

// Setup test environment
beforeEach(() => {
  vi.clearAllMocks()
})