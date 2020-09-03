import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import Logging from './Logging';

describe('<Logging />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<Logging />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('Card').text()).toContain('Logging settings');
  });
});
