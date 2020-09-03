import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import ActivityStream from './ActivityStream';

describe('<ActivityStream />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<ActivityStream />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('Card').text()).toContain('Activity stream settings');
  });
});
