module.exports = {
  collectCoverageFrom: [
    'src/**/*.{js,jsx}'
  ],
  moduleNameMapper: {
    '^[./a-zA-Z0-9$_-]+\\.svg$': '<rootDir>/__tests__/stubs/svgStub.js'
  },
  setupTestFrameworkScriptFile: '<rootDir>/jest.setup.js',
  testMatch: [
    '<rootDir>/__tests__/tests/**/*.{js,jsx}'
  ],
  testEnvironment: 'jsdom',
  testURL: 'http://127.0.0.1:3001',
  transform: {
    '^.+\\.(js|jsx)$': 'babel-jest'
  },
  transformIgnorePatterns: [
    '[/\\\\]node_modules[/\\\\].+\\.(?!(axios)/)(js|jsx)$'
  ]
};
