module.exports = {
  collectCoverageFrom: [
    'src/**/*.{js,jsx}'
  ],
  coveragePathIgnorePatterns: [
    '<rootDir>/src/locales',
    'index.js'
  ],
  moduleNameMapper: {
    '\\.(css|scss|less)$': '<rootDir>/__mocks__/styleMock.js',
    '^@api(.*)$': '<rootDir>/src/api$1',
    '^@components(.*)$': '<rootDir>/src/components$1',
    '^@contexts(.*)$': '<rootDir>/src/contexts$1',
    '^@screens(.*)$': '<rootDir>/src/screens$1',
    '^@util(.*)$': '<rootDir>/src/util$1',
    '^@types(.*)$': '<rootDir>/src/types$1',
    '^@testUtils(.*)$': '<rootDir>/testUtils$1',
  },
  setupFiles: [
    '@nteract/mockument'
  ],
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  snapshotSerializers: [
    "enzyme-to-json/serializer"
  ],
  testMatch: [
    '<rootDir>/**/*.test.{js,jsx}'
  ],
  testEnvironment: 'jsdom',
  testURL: 'http://127.0.0.1:3001',
  transform: {
    '^.+\\.(js|jsx)$': 'babel-jest',
    '\\.(jpg|jpeg|png|gif|eot|otf|webp|svg|ttf|woff|woff2|mp4|webm|wav|mp3|m4a|aac|oga)$': '<rootDir>/__mocks__/fileMock.js',
  },
  transformIgnorePatterns: [
    '[/\\\\]node_modules[/\\\\].+\\.(?!(axios)/)(js|jsx)$'
  ],
  watchPathIgnorePatterns: [
    '<rootDir>/node_modules'
  ]
};
