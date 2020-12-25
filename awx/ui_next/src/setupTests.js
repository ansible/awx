import { configure } from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';

require('@babel/polyfill');

configure({ adapter: new Adapter() });

jest.setTimeout(5000 * 4);

// apply polyfills for jsdom
require('@nteract/mockument');

// eslint-disable-next-line import/prefer-default-export
export const asyncFlush = () => new Promise(resolve => setImmediate(resolve));

// this ensures that debug messages don't get logged out to the console
// while tests are running i.e. websocket connect/disconnect
global.console = {
  ...console,
  debug: jest.fn(),
};

// This global variable is part of our Content Security Policy framework
// and so this mock ensures that we don't encounter a reference error
// when running the tests
global.__webpack_nonce__ = null;
