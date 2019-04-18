module.exports = {
  collectCoverageFrom: [
    'src/**/*.{js,jsx}'
  ],
  coveragePathIgnorePatterns: [
    '<rootDir>/src/locales'
  ],
  moduleNameMapper: {
    '\\.(css|scss|less)$': '<rootDir>/__mocks__/styleMock.js'
  },
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  snapshotSerializers: [
    "enzyme-to-json/serializer"
  ],
  testMatch: [
    '<rootDir>/__tests__/**/*.test.{js,jsx}'
  ],
  testEnvironment: 'jsdom',
  testURL: 'http://127.0.0.1:3001',
  transform: {
    '^.+\\.(js|jsx)$': 'babel-jest',
    '\\.(jpg|jpeg|png|gif|eot|otf|webp|svg|ttf|woff|woff2|mp4|webm|wav|mp3|m4a|aac|oga)$': '<rootDir>/__mocks__/fileMock.js',
  },
  transformIgnorePatterns: [
    '[/\\\\]node_modules[/\\\\].+\\.(?!(axios)/)(js|jsx)$'
  ]
};
