import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { SettingsProvider } from 'contexts/Settings';
import { SettingsAPI } from 'api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import mockAllOptions from '../shared/data.allSettingOptions.json';
import GoogleOAuth2 from './GoogleOAuth2';

jest.mock('../../../api');

describe('<GoogleOAuth2 />', () => {
  let wrapper;

  beforeEach(() => {
    SettingsAPI.readCategory.mockResolvedValue({
      data: {
        SOCIAL_AUTH_GOOGLE_OAUTH2_CALLBACK_URL:
          'https://towerhost/sso/complete/google-oauth2/',
        SOCIAL_AUTH_GOOGLE_OAUTH2_KEY: 'mock key',
        SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET: '$encrypted$',
        SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS: [
          'example.com',
          'example_2.com',
        ],
        SOCIAL_AUTH_GOOGLE_OAUTH2_AUTH_EXTRA_ARGUMENTS: {},
        SOCIAL_AUTH_GOOGLE_OAUTH2_ORGANIZATION_MAP: {
          Default: {},
        },
        SOCIAL_AUTH_GOOGLE_OAUTH2_TEAM_MAP: {},
      },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should render Google OAuth 2.0 details', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/google_oauth2/details'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <GoogleOAuth2 />
        </SettingsProvider>,
        {
          context: { router: { history } },
        }
      );
    });
    expect(wrapper.find('GoogleOAuth2Detail').length).toBe(1);
  });

  test('should render Google OAuth 2.0 edit', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/google_oauth2/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <GoogleOAuth2 />
        </SettingsProvider>,
        {
          context: { router: { history } },
        }
      );
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
