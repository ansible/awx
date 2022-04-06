module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['./src/setupTests.js'],
  rootDir: '../',
  roots: ['<rootDir>'],
  moduleNameMapper: {
    '\\.(css|styl|less|sass|scss)$': '<rootDir>/__mocks__/styleMock.js',
  },
  modulePaths: ['<rootDir>'],
  moduleDirectories: ['node_modules', 'src'],
  snapshotSerializers: ['enzyme-to-json/serializer'],
  collectCoverageFrom: [
    '<rootDir>/src/**/*.{js,jsx}',
    '<rootDir>/testUtils/**/*.{js,jsx}',
  ],
  coveragePathIgnorePatterns: ['<rootDir>/src/locales', 'index.js'],
  transformIgnorePatterns: [
    '<rootDir>/node_modules/(?!d3)/',
    '<rootDir>/node_modules/(?!has-ansi)/',
  ],
};
