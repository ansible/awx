import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import SAML from './SAML';

describe('<SAML />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<SAML />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('Card').text()).toContain('SAML settings');
  });
});
