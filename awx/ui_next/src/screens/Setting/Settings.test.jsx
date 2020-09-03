import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import Settings from './Settings';

describe('<Settings />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<Settings />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.length).toBe(1);
  });
});
