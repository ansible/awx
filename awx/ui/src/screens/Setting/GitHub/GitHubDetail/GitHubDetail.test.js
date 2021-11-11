import React from 'react';
import { act } from 'react-dom/test-utils';
import { useRouteMatch } from 'react-router-dom';
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
import GitHubDetail from './GitHubDetail';

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useRouteMatch: jest.fn(),
}));
jest.mock('../../../../api');

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
const mockEnterprise = {
  data: {
    SOCIAL_AUTH_GITHUB_ENTERPRISE_CALLBACK_URL:
      'https://towerhost/sso/complete/github-enterprise/',
    SOCIAL_AUTH_GITHUB_ENTERPRISE_URL: 'https://localhost/enterpriseurl',
    SOCIAL_AUTH_GITHUB_ENTERPRISE_API_URL: 'https://localhost/enterpriseapi',
    SOCIAL_AUTH_GITHUB_ENTERPRISE_KEY: 'foobar',
    SOCIAL_AUTH_GITHUB_ENTERPRISE_SECRET: '$encrypted$',
    SOCIAL_AUTH_GITHUB_ENTERPRISE_ORGANIZATION_MAP: null,
    SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_MAP: null,
  },
};
const mockEnterpriseOrg = {
  data: {
    SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_CALLBACK_URL:
      'https://towerhost/sso/complete/github-enterprise-org/',
    SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_URL: 'https://localhost/orgurl',
    SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_API_URL: 'https://localhost/orgapi',
    SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_KEY: 'foobar',
    SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_SECRET: '$encrypted$',
    SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_NAME: 'foo',
    SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_ORGANIZATION_MAP: null,
    SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_TEAM_MAP: null,
  },
};
const mockEnterpriseTeam = {
  data: {
    SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_CALLBACK_URL:
      'https://towerhost/sso/complete/github-enterprise-team/',
    SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_URL: 'https://localhost/teamurl',
    SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_API_URL: 'https://localhost/teamapi',
    SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_KEY: 'foobar',
    SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_SECRET: '$encrypted$',
    SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_ID: 'foo',
    SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_ORGANIZATION_MAP: null,
    SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_TEAM_MAP: null,
  },
};

describe('<GitHubDetail />', () => {
  describe('Default', () => {
    let wrapper;

    beforeEach(async () => {
      SettingsAPI.readCategory.mockResolvedValueOnce(mockDefault);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockOrg);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockTeam);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockEnterprise);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockEnterpriseOrg);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockEnterpriseTeam);
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
      await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    });

    afterAll(() => {
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
        'GitHub Enterprise',
        'GitHub Enterprise Organization',
        'GitHub Enterprise Team',
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
      assertVariableDetail(wrapper, 'GitHub OAuth2 Organization Map', 'null');
      assertVariableDetail(wrapper, 'GitHub OAuth2 Team Map', 'null');
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
      await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
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
      await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
      expect(wrapper.find('ContentError').length).toBe(1);
    });
  });

  describe('Organization', () => {
    let wrapper;

    beforeAll(async () => {
      SettingsAPI.readCategory.mockResolvedValueOnce(mockDefault);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockOrg);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockTeam);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockEnterprise);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockEnterpriseOrg);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockEnterpriseTeam);
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
      await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    });

    afterAll(() => {
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
        'null'
      );
      assertVariableDetail(
        wrapper,
        'GitHub Organization OAuth2 Team Map',
        'null'
      );
    });
  });

  describe('Team', () => {
    let wrapper;

    beforeAll(async () => {
      SettingsAPI.readCategory.mockResolvedValueOnce(mockDefault);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockOrg);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockTeam);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockEnterprise);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockEnterpriseOrg);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockEnterpriseTeam);
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
      await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    });

    afterAll(() => {
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

  describe('Enterprise', () => {
    let wrapper;

    beforeAll(async () => {
      SettingsAPI.readCategory.mockResolvedValueOnce(mockDefault);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockOrg);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockTeam);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockEnterprise);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockEnterpriseOrg);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockEnterpriseTeam);
      useRouteMatch.mockImplementation(() => ({
        url: '/settings/github/enterprise/details',
        path: '/settings/github/:category/details',
        params: { category: 'enterprise' },
      }));
      await act(async () => {
        wrapper = mountWithContexts(
          <SettingsProvider value={mockAllOptions.actions}>
            <GitHubDetail />
          </SettingsProvider>
        );
      });
      await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    });

    afterAll(() => {
      jest.clearAllMocks();
    });

    test('should render expected details', () => {
      assertDetail(
        wrapper,
        'GitHub Enterprise OAuth2 Callback URL',
        'https://towerhost/sso/complete/github-enterprise/'
      );
      assertDetail(
        wrapper,
        'GitHub Enterprise URL',
        'https://localhost/enterpriseurl'
      );
      assertDetail(
        wrapper,
        'GitHub Enterprise API URL',
        'https://localhost/enterpriseapi'
      );
      assertDetail(wrapper, 'GitHub Enterprise OAuth2 Key', 'foobar');
      assertDetail(wrapper, 'GitHub Enterprise OAuth2 Secret', 'Encrypted');
      assertVariableDetail(
        wrapper,
        'GitHub Enterprise OAuth2 Organization Map',
        'null'
      );
      assertVariableDetail(
        wrapper,
        'GitHub Enterprise OAuth2 Team Map',
        'null'
      );
    });
  });

  describe('Enterprise Org', () => {
    let wrapper;

    beforeAll(async () => {
      SettingsAPI.readCategory.mockResolvedValueOnce(mockDefault);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockOrg);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockTeam);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockEnterprise);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockEnterpriseOrg);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockEnterpriseTeam);
      useRouteMatch.mockImplementation(() => ({
        url: '/settings/github/enterprise_organization/details',
        path: '/settings/github/:category/details',
        params: { category: 'enterprise_organization' },
      }));
      await act(async () => {
        wrapper = mountWithContexts(
          <SettingsProvider value={mockAllOptions.actions}>
            <GitHubDetail />
          </SettingsProvider>
        );
      });
      await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    });

    afterAll(() => {
      jest.clearAllMocks();
    });

    test('should render expected details', () => {
      assertDetail(
        wrapper,
        'GitHub Enterprise Organization OAuth2 Callback URL',
        'https://towerhost/sso/complete/github-enterprise-org/'
      );
      assertDetail(
        wrapper,
        'GitHub Enterprise Organization URL',
        'https://localhost/orgurl'
      );
      assertDetail(
        wrapper,
        'GitHub Enterprise Organization API URL',
        'https://localhost/orgapi'
      );
      assertDetail(
        wrapper,
        'GitHub Enterprise Organization OAuth2 Key',
        'foobar'
      );
      assertDetail(
        wrapper,
        'GitHub Enterprise Organization OAuth2 Secret',
        'Encrypted'
      );
      assertDetail(wrapper, 'GitHub Enterprise Organization Name', 'foo');
      assertVariableDetail(
        wrapper,
        'GitHub Enterprise Organization OAuth2 Organization Map',
        'null'
      );
      assertVariableDetail(
        wrapper,
        'GitHub Enterprise Organization OAuth2 Team Map',
        'null'
      );
    });
  });

  describe('Enterprise Team', () => {
    let wrapper;

    beforeAll(async () => {
      SettingsAPI.readCategory.mockResolvedValueOnce(mockDefault);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockOrg);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockTeam);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockEnterprise);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockEnterpriseOrg);
      SettingsAPI.readCategory.mockResolvedValueOnce(mockEnterpriseTeam);
      useRouteMatch.mockImplementation(() => ({
        url: '/settings/github/enterprise_team/details',
        path: '/settings/github/:category/details',
        params: { category: 'enterprise_team' },
      }));
      await act(async () => {
        wrapper = mountWithContexts(
          <SettingsProvider value={mockAllOptions.actions}>
            <GitHubDetail />
          </SettingsProvider>
        );
      });
      await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    });

    afterAll(() => {
      jest.clearAllMocks();
    });

    test('should render expected details', () => {
      assertDetail(
        wrapper,
        'GitHub Enterprise Team OAuth2 Callback URL',
        'https://towerhost/sso/complete/github-enterprise-team/'
      );
      assertDetail(
        wrapper,
        'GitHub Enterprise Team URL',
        'https://localhost/teamurl'
      );
      assertDetail(
        wrapper,
        'GitHub Enterprise Team API URL',
        'https://localhost/teamapi'
      );
      assertDetail(wrapper, 'GitHub Enterprise Team OAuth2 Key', 'foobar');
      assertDetail(
        wrapper,
        'GitHub Enterprise Team OAuth2 Secret',
        'Encrypted'
      );
      assertDetail(wrapper, 'GitHub Enterprise Team ID', 'foo');
      assertVariableDetail(
        wrapper,
        'GitHub Enterprise Team OAuth2 Organization Map',
        'null'
      );
      assertVariableDetail(
        wrapper,
        'GitHub Enterprise Team OAuth2 Team Map',
        'null'
      );
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
