import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import Jobs from './Jobs';

describe('<Jobs />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<Jobs />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('Card').text()).toContain('Jobs settings');
  });
});
