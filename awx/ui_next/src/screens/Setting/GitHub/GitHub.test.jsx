import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import GitHub from './GitHub';

describe('<GitHub />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<GitHub />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('Card').text()).toContain('GitHub settings');
  });
});
