import React from 'react';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import LDAPDetail from './LDAPDetail';

describe('<LDAPDetail />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<LDAPDetail />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('LDAPDetail').length).toBe(1);
  });
});
