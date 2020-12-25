import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import GoogleOAuth2 from './GoogleOAuth2';

import { SettingsAPI } from '../../../api';

jest.mock('../../../api/models/Settings');
SettingsAPI.readCategory.mockResolvedValue({
  data: {},
});

describe('<GoogleOAuth2 />', () => {
  let wrapper;

  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('should render Google OAuth 2.0 details', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/google_oauth2/details'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<GoogleOAuth2 />, {
        context: { router: { history } },
      });
    });
    expect(wrapper.find('GoogleOAuth2Detail').length).toBe(1);
  });

  test('should render Google OAuth 2.0 edit', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/google_oauth2/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<GoogleOAuth2 />, {
        context: { router: { history } },
      });
    });
    expect(wrapper.find('GoogleOAuth2Edit').length).toBe(1);
  });

  test('should show content error when user navigates to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/google_oauth2/foo'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<GoogleOAuth2 />, {
        context: { router: { history } },
      });
    });
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
