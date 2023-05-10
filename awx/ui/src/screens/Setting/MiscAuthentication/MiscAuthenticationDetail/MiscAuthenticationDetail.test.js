import React from 'react';
import { act } from 'react-dom/test-utils';
import { SettingsProvider } from 'contexts/Settings';
import { SettingsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../../testUtils/enzymeHelpers';
import {
  assertDetail,
  assertVariableDetail,
} from '../../shared/settingTestUtils';
import mockAllOptions from '../../shared/data.allSettingOptions.json';
import MiscAuthenticationDetail from './MiscAuthenticationDetail';

jest.mock('../../../../api');

describe('<MiscAuthenticationDetail />', () => {
  let wrapper;

  beforeEach(async () => {
    SettingsAPI.readCategory = jest.fn();
    SettingsAPI.readCategory.mockResolvedValue({
      data: {
        SESSION_COOKIE_AGE: 1800,
        SESSIONS_PER_USER: -1,
        DISABLE_LOCAL_AUTH: false,
        AUTH_BASIC_ENABLED: true,
        OAUTH2_PROVIDER: {
          ACCESS_TOKEN_EXPIRE_SECONDS: 31536000000,
          REFRESH_TOKEN_EXPIRE_SECONDS: 2628000,
          AUTHORIZATION_CODE_EXPIRE_SECONDS: 600,
        },
        ALLOW_OAUTH2_FOR_EXTERNAL_USERS: false,
        LOGIN_REDIRECT_OVERRIDE: 'https://foohost',
        AUTHENTICATION_BACKENDS: [
          'awx.sso.backends.TACACSPlusBackend',
          'awx.main.backends.AWXModelBackend',
        ],
        SOCIAL_AUTH_ORGANIZATION_MAP: {},
        SOCIAL_AUTH_TEAM_MAP: {},
        SOCIAL_AUTH_USER_FIELDS: [],
        SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL: false,
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <MiscAuthenticationDetail />
        </SettingsProvider>
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
  });

  test('initially renders without crashing', () => {
    expect(wrapper.find('MiscAuthenticationDetail').length).toBe(1);
  });

  test('should render expected tabs', () => {
    const expectedTabs = ['Back to Settings', 'Details'];
    wrapper.find('RoutedTabs li').forEach((tab, index) => {
      expect(tab.text()).toEqual(expectedTabs[index]);
    });
  });

  test('should render expected details', () => {
    assertDetail(wrapper, 'Disable the built-in authentication system', 'Off');
    assertVariableDetail(
      wrapper,
      'OAuth 2 Timeout Settings',
      '{\n  "ACCESS_TOKEN_EXPIRE_SECONDS": 31536000000,\n  "AUTHORIZATION_CODE_EXPIRE_SECONDS": 600,\n  "REFRESH_TOKEN_EXPIRE_SECONDS": 2628000\n}'
    );
    assertDetail(wrapper, 'Login redirect override URL', 'https://foohost');
    assertVariableDetail(
      wrapper,
      'Authentication Backends',
      '[\n  "awx.sso.backends.TACACSPlusBackend",\n  "awx.main.backends.AWXModelBackend"\n]'
    );
    assertVariableDetail(wrapper, 'Social Auth Organization Map', '{}');
    assertVariableDetail(wrapper, 'Social Auth Team Map', '{}');
    assertVariableDetail(wrapper, 'Social Auth User Fields', '[]');
    assertDetail(wrapper, 'Use Email address for usernames', 'Off');
    assertDetail(
      wrapper,
      'Allow External Users to Create OAuth2 Tokens',
      'Off'
    );
    assertDetail(wrapper, 'Enable HTTP Basic Auth', 'On');
    assertDetail(wrapper, 'Idle Time Force Log Out', '1800 seconds');
    assertDetail(
      wrapper,
      'Maximum number of simultaneous logged in sessions',
      '-1'
    );
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
          <MiscAuthenticationDetail />
        </SettingsProvider>,
        {
          context: { config },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('Button[aria-label="Edit"]').exists()).toBeFalsy();
  });

  test('should display content error when api throws error on initial render', async () => {
    SettingsAPI.readCategory.mockRejectedValue(new Error());
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <MiscAuthenticationDetail />
        </SettingsProvider>
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
