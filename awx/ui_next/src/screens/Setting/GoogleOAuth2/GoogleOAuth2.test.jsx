import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import GoogleOAuth2 from './GoogleOAuth2';

describe('<GoogleOAuth2 />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<GoogleOAuth2 />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('Card').text()).toContain('Google OAuth 2.0 settings');
  });
});
