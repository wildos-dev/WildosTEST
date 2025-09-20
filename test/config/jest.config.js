/** @type {import('jest').Config} */
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/test'],
  testMatch: [
    '<rootDir>/test/**/__tests__/**/*.(ts|tsx|js)',
    '<rootDir>/test/**/(*.)+(spec|test).(ts|tsx|js)'
  ],
  transform: {
    '^.+\\.(ts|tsx)$': 'ts-jest',
    '^.+\\.(js|jsx)$': 'babel-jest'
  },
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/dashboard/src/$1',
    '^@assets/(.*)$': '<rootDir>/dashboard/src/assets/$1',
    '^@lib/(.*)$': '<rootDir>/dashboard/src/libs/$1',
    '^@components/(.*)$': '<rootDir>/dashboard/src/common/components/$1',
    '^@features/(.*)$': '<rootDir>/dashboard/src/features/$1',
    '^@modules/(.*)$': '<rootDir>/dashboard/src/modules/$1',
    '^@hooks/(.*)$': '<rootDir>/dashboard/src/common/hooks/$1',
    '^@utils/(.*)$': '<rootDir>/dashboard/src/common/utils/$1',
    '^@types/(.*)$': '<rootDir>/dashboard/src/common/types/$1',
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    '\\.(jpg|jpeg|png|gif|svg)$': '<rootDir>/test/__mocks__/fileMock.js'
  },
  setupFilesAfterEnv: ['<rootDir>/test/config/jest.setup.ts'],
  coverageDirectory: '<rootDir>/test/coverage',
  collectCoverageFrom: [
    'dashboard/src/**/*.{ts,tsx}',
    '!dashboard/src/**/*.d.ts',
    '!dashboard/src/**/*.test.{ts,tsx}',
    '!dashboard/src/**/*.spec.{ts,tsx}',
    '!dashboard/src/main.tsx',
    '!dashboard/src/vite-env.d.ts'
  ],
  coverageReporters: ['text', 'lcov', 'html'],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  },
  testTimeout: 10000,
  verbose: true
}