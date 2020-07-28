import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import TACACS from './TACACS';

describe('<TACACS />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<TACACS />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('Card').text()).toContain('TACACS+ settings');
  });
});
