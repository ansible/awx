import React from 'react';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import GoogleOAuth2Detail from './GoogleOAuth2Detail';

describe('<GoogleOAuth2Detail />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<GoogleOAuth2Detail />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('GoogleOAuth2Detail').length).toBe(1);
  });
});
