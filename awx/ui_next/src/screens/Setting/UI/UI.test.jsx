import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import UI from './UI';

describe('<UI />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<UI />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('Card').text()).toContain('User interface settings');
  });
});
