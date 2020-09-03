import React from 'react';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import LDAPEdit from './LDAPEdit';

describe('<LDAPEdit />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<LDAPEdit />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('LDAPEdit').length).toBe(1);
  });
});
