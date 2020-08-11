import React from 'react';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import GoogleOAuth2Edit from './GoogleOAuth2Edit';

describe('<GoogleOAuth2Edit />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<GoogleOAuth2Edit />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('GoogleOAuth2Edit').length).toBe(1);
  });
});
