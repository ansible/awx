import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import MiscSystem from './MiscSystem';

describe('<MiscSystem />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<MiscSystem />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('Card').text()).toContain(
      'Miscellaneous system settings'
    );
  });
});
