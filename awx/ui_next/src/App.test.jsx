import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../testUtils/enzymeHelpers';

import App from './App';

jest.mock('./api');

describe('<App />', () => {
  test('renders ok', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<App />);
    });
    expect(wrapper.length).toBe(1);
  });
});
