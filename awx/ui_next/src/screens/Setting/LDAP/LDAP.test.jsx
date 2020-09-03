import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import LDAP from './LDAP';

describe('<LDAP />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<LDAP />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('Card').text()).toContain('LDAP settings');
  });
});
