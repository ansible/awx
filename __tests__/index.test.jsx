import React from 'react';
import ReactDOM from 'react-dom';

import api from '../src/api';

import { main } from '../src/index';

const custom_logo = (<div>logo</div>);
const custom_login_info = 'custom login info';

jest.mock('react-dom', () => ({ render: jest.fn() }));

describe('index.jsx', () => {
  test('renders without crashing', async () => {
    api.getRoot = jest.fn().mockImplementation(() => Promise
      .resolve({ data: { custom_logo, custom_login_info } }));

    await main();

    expect(ReactDOM.render).toHaveBeenCalled();
  });
});
