import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import AzureAD from './AzureAD';

describe('<AzureAD />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<AzureAD />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('Card').text()).toContain('Azure AD settings');
  });
});
