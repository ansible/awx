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
import AzureADDetail from './AzureADDetail';

jest.mock('../../../../api/models/Settings');
SettingsAPI.readCategory.mockResolvedValue({
  data: {
    SOCIAL_AUTH_AZUREAD_OAUTH2_CALLBACK_URL:
      'https://towerhost/sso/complete/azuread-oauth2/',
    SOCIAL_AUTH_AZUREAD_OAUTH2_KEY: 'mock key',
    SOCIAL_AUTH_AZUREAD_OAUTH2_SECRET: '$encrypted$',
    SOCIAL_AUTH_AZUREAD_OAUTH2_ORGANIZATION_MAP: {},
    SOCIAL_AUTH_AZUREAD_OAUTH2_TEAM_MAP: {
      'My Team': {
        users: [],
      },
    },
  },
});

describe('<AzureADDetail />', () => {
  let wrapper;

  beforeAll(async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <AzureADDetail />
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
    expect(wrapper.find('AzureADDetail').length).toBe(1);
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
      'Azure AD OAuth2 Callback URL',
      'https://towerhost/sso/complete/azuread-oauth2/'
    );
    assertDetail(wrapper, 'Azure AD OAuth2 Key', 'mock key');
    assertDetail(wrapper, 'Azure AD OAuth2 Secret', 'Encrypted');
    assertVariableDetail(wrapper, 'Azure AD OAuth2 Organization Map', '{}');
    assertVariableDetail(
      wrapper,
      'Azure AD OAuth2 Team Map',
      '{\n  "My Team": {\n    "users": []\n  }\n}'
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
          <AzureADDetail />
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
          <AzureADDetail />
        </SettingsProvider>
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
