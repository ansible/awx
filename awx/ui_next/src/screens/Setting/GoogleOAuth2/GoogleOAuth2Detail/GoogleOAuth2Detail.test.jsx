import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../../testUtils/enzymeHelpers';
import { SettingsProvider } from '../../../../contexts/Settings';
import { SettingsAPI } from '../../../../api';
import {
  assertDetail,
  assertVariableDetail,
} from '../../shared/settingTestUtils';
import mockAllOptions from '../../shared/data.allSettingOptions.json';
import GoogleOAuth2Detail from './GoogleOAuth2Detail';

jest.mock('../../../../api/models/Settings');
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

describe('<GoogleOAuth2Detail />', () => {
  let wrapper;

  beforeAll(async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <GoogleOAuth2Detail />
        </SettingsProvider>
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
  });

  afterAll(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('initially renders without crashing', () => {
    expect(wrapper.find('GoogleOAuth2Detail').length).toBe(1);
  });

  test('should render expected tabs', () => {
    const expectedTabs = ['Back to Settings', 'Details'];
    wrapper.find('RoutedTabs li').forEach((tab, index) => {
      expect(tab.text()).toEqual(expectedTabs[index]);
    });
  });

  test('should render expected details', () => {
    assertDetail(
      wrapper,
      'Google OAuth2 Callback URL',
      'https://towerhost/sso/complete/google-oauth2/'
    );
    assertDetail(wrapper, 'Google OAuth2 Key', 'mock key');
    assertDetail(wrapper, 'Google OAuth2 Secret', 'Encrypted');
    assertVariableDetail(
      wrapper,
      'Google OAuth2 Allowed Domains',
      '[\n  "example.com",\n  "example_2.com"\n]'
    );
    assertVariableDetail(wrapper, 'Google OAuth2 Extra Arguments', '{}');
    assertVariableDetail(
      wrapper,
      'Google OAuth2 Organization Map',
      '{\n  "Default": {}\n}'
    );
    assertVariableDetail(wrapper, 'Google OAuth2 Team Map', '{}');
  });

  test('should hide edit button from non-superusers', async () => {
    const config = {
      me: {
        is_superuser: false,
      },
    };
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <GoogleOAuth2Detail />
        </SettingsProvider>,
        {
          context: { config },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('Button[aria-label="Edit"]').exists()).toBeFalsy();
  });

  test('should display content error when api throws error on initial render', async () => {
    SettingsAPI.readCategory.mockRejectedValue(new Error());
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <GoogleOAuth2Detail />
        </SettingsProvider>
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
