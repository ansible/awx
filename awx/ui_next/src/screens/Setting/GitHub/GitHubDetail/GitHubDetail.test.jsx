import React from 'react';
import { act } from 'react-dom/test-utils';
import { useRouteMatch } from 'react-router-dom';
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
import GitHubDetail from './GitHubDetail';

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useRouteMatch: jest.fn(),
}));
jest.mock('../../../../api/models/Settings');

const mockDefault = {
  data: {
    SOCIAL_AUTH_GITHUB_CALLBACK_URL: 'https://towerhost/sso/complete/github/',
    SOCIAL_AUTH_GITHUB_KEY: 'mock github key',
    SOCIAL_AUTH_GITHUB_SECRET: '$encrypted$',
    SOCIAL_AUTH_GITHUB_ORGANIZATION_MAP: null,
    SOCIAL_AUTH_GITHUB_TEAM_MAP: null,
  },
};
const mockOrg = {
  data: {
    SOCIAL_AUTH_GITHUB_ORG_CALLBACK_URL:
      'https://towerhost/sso/complete/github-org/',
    SOCIAL_AUTH_GITHUB_ORG_KEY: '',
    SOCIAL_AUTH_GITHUB_ORG_SECRET: '$encrypted$',
    SOCIAL_AUTH_GITHUB_ORG_NAME: '',
    SOCIAL_AUTH_GITHUB_ORG_ORGANIZATION_MAP: null,
    SOCIAL_AUTH_GITHUB_ORG_TEAM_MAP: null,
  },
};
const mockTeam = {
  data: {
    SOCIAL_AUTH_GITHUB_TEAM_CALLBACK_URL:
      'https://towerhost/sso/complete/github-team/',
    SOCIAL_AUTH_GITHUB_TEAM_KEY: 'OAuth2 key (Client ID)',
    SOCIAL_AUTH_GITHUB_TEAM_SECRET: '$encrypted$',
    SOCIAL_AUTH_GITHUB_TEAM_ID: 'team_id',
    SOCIAL_AUTH_GITHUB_TEAM_ORGANIZATION_MAP: {},
    SOCIAL_AUTH_GITHUB_TEAM_TEAM_MAP: {},
  },
};

describe('<GitHubDetail />', () => {
  describe('Default', () => {
    let wrapper;

    beforeAll(async () => {
      SettingsAPI.readCategory.mockResolvedValueOnce(mockDefault);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockOrg);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockTeam);
      useRouteMatch.mockImplementation(() => ({
        url: '/settings/github/default/details',
        path: '/settings/github/:category/details',
        params: { category: 'default' },
      }));
      await act(async () => {
        wrapper = mountWithContexts(
          <SettingsProvider value={mockAllOptions.actions}>
            <GitHubDetail />
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
      expect(wrapper.find('GitHubDetail').length).toBe(1);
    });

    test('should render expected tabs', () => {
      const expectedTabs = [
        'Back to Settings',
        'GitHub Default',
        'GitHub Organization',
        'GitHub Team',
      ];
      wrapper.find('RoutedTabs li').forEach((tab, index) => {
        expect(tab.text()).toEqual(expectedTabs[index]);
      });
    });

    test('should render expected details', () => {
      assertDetail(
        wrapper,
        'GitHub OAuth2 Callback URL',
        'https://towerhost/sso/complete/github/'
      );
      assertDetail(wrapper, 'GitHub OAuth2 Key', 'mock github key');
      assertDetail(wrapper, 'GitHub OAuth2 Secret', 'Encrypted');
      assertVariableDetail(wrapper, 'GitHub OAuth2 Organization Map', '{}');
      assertVariableDetail(wrapper, 'GitHub OAuth2 Team Map', '{}');
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
            <GitHubDetail />
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
            <GitHubDetail />
          </SettingsProvider>
        );
      });
      await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
      expect(wrapper.find('ContentError').length).toBe(1);
    });
  });

  describe('Organization', () => {
    let wrapper;

    beforeAll(async () => {
      SettingsAPI.readCategory.mockResolvedValueOnce(mockDefault);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockOrg);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockTeam);
      useRouteMatch.mockImplementation(() => ({
        url: '/settings/github/organization/details',
        path: '/settings/github/:category/details',
        params: { category: 'organization' },
      }));
      await act(async () => {
        wrapper = mountWithContexts(
          <SettingsProvider value={mockAllOptions.actions}>
            <GitHubDetail />
          </SettingsProvider>
        );
      });
      await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    });

    afterAll(() => {
      wrapper.unmount();
      jest.clearAllMocks();
    });

    test('should render expected details', () => {
      assertDetail(
        wrapper,
        'GitHub Organization OAuth2 Callback URL',
        'https://towerhost/sso/complete/github-org/'
      );
      assertDetail(wrapper, 'GitHub Organization OAuth2 Key', 'Not configured');
      assertDetail(wrapper, 'GitHub Organization OAuth2 Secret', 'Encrypted');
      assertDetail(wrapper, 'GitHub Organization Name', 'Not configured');
      assertVariableDetail(
        wrapper,
        'GitHub Organization OAuth2 Organization Map',
        '{}'
      );
      assertVariableDetail(
        wrapper,
        'GitHub Organization OAuth2 Team Map',
        '{}'
      );
    });
  });

  describe('Team', () => {
    let wrapper;

    beforeAll(async () => {
      SettingsAPI.readCategory.mockResolvedValueOnce(mockDefault);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockOrg);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockTeam);
      useRouteMatch.mockImplementation(() => ({
        url: '/settings/github/team/details',
        path: '/settings/github/:category/details',
        params: { category: 'team' },
      }));
      await act(async () => {
        wrapper = mountWithContexts(
          <SettingsProvider value={mockAllOptions.actions}>
            <GitHubDetail />
          </SettingsProvider>
        );
      });
      await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    });

    afterAll(() => {
      wrapper.unmount();
      jest.clearAllMocks();
    });

    test('should render expected details', () => {
      assertDetail(
        wrapper,
        'GitHub Team OAuth2 Callback URL',
        'https://towerhost/sso/complete/github-team/'
      );
      assertDetail(wrapper, 'GitHub Team OAuth2 Key', 'OAuth2 key (Client ID)');
      assertDetail(wrapper, 'GitHub Team OAuth2 Secret', 'Encrypted');
      assertDetail(wrapper, 'GitHub Team ID', 'team_id');
      assertVariableDetail(
        wrapper,
        'GitHub Team OAuth2 Organization Map',
        '{}'
      );
      assertVariableDetail(wrapper, 'GitHub Team OAuth2 Team Map', '{}');
    });
  });

  describe('Redirect', () => {
    test('should render redirect when user navigates to erroneous category', async () => {
      let wrapper;
      useRouteMatch.mockImplementation(() => ({
        url: '/settings/github/foo/details',
        path: '/settings/github/:category/details',
        params: { category: 'foo' },
      }));
      await act(async () => {
        wrapper = mountWithContexts(
          <SettingsProvider value={mockAllOptions.actions}>
            <GitHubDetail />
          </SettingsProvider>
        );
      });
      await waitForElement(wrapper, 'Redirect');
    });
  });
});
