import { configure } from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';

require('@babel/polyfill');

configure({ adapter: new Adapter() });

jest.setTimeout(5000 * 4);

// apply polyfills for jsdom
require('@nteract/mockument');

// eslint-disable-next-line import/prefer-default-export
export const asyncFlush = () => new Promise(resolve => setImmediate(resolve));
