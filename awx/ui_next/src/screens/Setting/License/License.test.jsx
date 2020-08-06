import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import License from './License';

describe('<License />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<License />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('Card').text()).toContain('License settings');
  });
});
