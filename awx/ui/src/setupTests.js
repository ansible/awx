import React from 'react';
import { configure } from 'enzyme';
import Adapter from '@wojtekmaj/enzyme-adapter-react-17';

require('@babel/polyfill');

configure({ adapter: new Adapter() });

jest.setTimeout(120000);

// apply polyfills for jsdom
require('@nteract/mockument');

// eslint-disable-next-line import/prefer-default-export
export const asyncFlush = () => new Promise((resolve) => setImmediate(resolve));

let hasConsoleError = false;
let hasConsoleWarn = false;
let networkRequestUrl = false;
const { error, warn } = global.console;

global.console = {
  ...console,
  // this ensures that debug messages don't get logged out to the console
  // while tests are running i.e. websocket connect/disconnect
  debug: jest.fn(),
  // fail tests that log errors.
  // adapted from https://github.com/facebook/jest/issues/6121#issuecomment-708330601
  error: (...args) => {
    if (!networkRequestUrl) {
      hasConsoleError = true;
      error(...args);
    }
  },
  warn: (...args) => {
    hasConsoleWarn = true;
    warn(...args);
  },
};

const logNetworkRequestError = (url) => {
  networkRequestUrl = url || true;
  return {
    status: 200,
    data: {},
  };
};

jest.mock('axios', () => ({
  create: () => ({
    get: logNetworkRequestError,
    post: logNetworkRequestError,
    delete: logNetworkRequestError,
    put: logNetworkRequestError,
    patch: logNetworkRequestError,
    options: logNetworkRequestError,
    interceptors: {
      response: {
        use: () => {},
      },
    },
  }),
}));

afterEach(() => {
  if (networkRequestUrl) {
    const url = networkRequestUrl;
    networkRequestUrl = false;
    throw new Error(
      `Network request was attempted to URL ${url} — API should be stubbed using jest.mock()`
    );
  }
  if (hasConsoleError) {
    hasConsoleError = false;
    throw new Error('Error logged to console');
  }
  if (hasConsoleWarn) {
    hasConsoleWarn = false;
    throw new Error('Warning logged to console');
  }
});

// This global variable is part of our Content Security Policy framework
// and so this mock ensures that we don't encounter a reference error
// when running the tests
global.__webpack_nonce__ = null;

const MockConfigContext = React.createContext({});
jest.doMock('./contexts/Config', () => ({
  __esModule: true,
  ConfigContext: MockConfigContext,
  ConfigProvider: MockConfigContext.Provider,
  Config: MockConfigContext.Consumer,
  useConfig: () => React.useContext(MockConfigContext),
  useAuthorizedPath: jest.fn(),
  useUserProfile: jest.fn(),
}));

// ?
const MockSessionContext = React.createContext({});
jest.doMock('./contexts/Session', () => ({
  __esModule: true,
  SessionContext: MockSessionContext,
  SessionProvider: MockSessionContext.Provider,
  useSession: () => React.useContext(MockSessionContext),
}));
