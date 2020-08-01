import React from 'react';

import { mountWithContexts } from '../testUtils/enzymeHelpers';

import App from './App';

jest.mock('./api');

describe('<App />', () => {
  test('renders ok', () => {
    const wrapper = mountWithContexts(<App />);
    expect(wrapper.length).toBe(1);
  });
});
