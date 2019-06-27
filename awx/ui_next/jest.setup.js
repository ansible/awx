require('@babel/polyfill');

// eslint-disable-next-line import/prefer-default-export
export const asyncFlush = () => new Promise((resolve) => setImmediate(resolve));

const enzyme = require('enzyme');
const Adapter = require('enzyme-adapter-react-16');

enzyme.configure({ adapter: new Adapter() });
