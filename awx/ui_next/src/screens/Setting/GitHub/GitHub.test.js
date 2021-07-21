import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { SettingsAPI } from 'api';
import { SettingsProvider } from 'contexts/Settings';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import mockAllOptions from '../shared/data.allSettingOptions.json';
import GitHub from './GitHub';

jest.mock('../../../api/models/Settings');

describe('<GitHub />', () => {
  let wrapper;

  beforeEach(() => {
    SettingsAPI.readCategory.mockResolvedValueOnce({
      data: {
        SOCIAL_AUTH_GITHUB_CALLBACK_URL:
          'https://towerhost/sso/complete/github/',
        SOCIAL_AUTH_GITHUB_KEY: 'mock github key',
        SOCIAL_AUTH_GITHUB_SECRET: '$encrypted$',
        SOCIAL_AUTH_GITHUB_ORGANIZATION_MAP: null,
        SOCIAL_AUTH_GITHUB_TEAM_MAP: null,
      },
    });
    SettingsAPI.readCategory.mockResolvedValueOnce({
      data: {
        SOCIAL_AUTH_GITHUB_ORG_CALLBACK_URL:
          'https://towerhost/sso/complete/github-org/',
        SOCIAL_AUTH_GITHUB_ORG_KEY: '',
        SOCIAL_AUTH_GITHUB_ORG_SECRET: '$encrypted$',
        SOCIAL_AUTH_GITHUB_ORG_NAME: '',
        SOCIAL_AUTH_GITHUB_ORG_ORGANIZATION_MAP: null,
        SOCIAL_AUTH_GITHUB_ORG_TEAM_MAP: null,
      },
    });
    SettingsAPI.readCategory.mockResolvedValueOnce({
      data: {
        SOCIAL_AUTH_GITHUB_TEAM_CALLBACK_URL:
          'https://towerhost/sso/complete/github-team/',
        SOCIAL_AUTH_GITHUB_TEAM_KEY: 'OAuth2 key (Client ID)',
        SOCIAL_AUTH_GITHUB_TEAM_SECRET: '$encrypted$',
        SOCIAL_AUTH_GITHUB_TEAM_ID: 'team_id',
        SOCIAL_AUTH_GITHUB_TEAM_ORGANIZATION_MAP: {},
        SOCIAL_AUTH_GITHUB_TEAM_TEAM_MAP: {},
      },
    });
    SettingsAPI.readCategory.mockResolvedValueOnce({
      data: {
        SOCIAL_AUTH_GITHUB_ENTERPRISE_CALLBACK_URL:
          'https://towerhost/sso/complete/github-enterprise/',
        SOCIAL_AUTH_GITHUB_ENTERPRISE_URL: 'https://localhost/url',
        SOCIAL_AUTH_GITHUB_ENTERPRISE_API_URL: 'https://localhost/apiurl',
        SOCIAL_AUTH_GITHUB_ENTERPRISE_KEY: 'ent_key',
        SOCIAL_AUTH_GITHUB_ENTERPRISE_SECRET: '$encrypted',
        SOCIAL_AUTH_GITHUB_ENTERPRISE_ORGANIZATION_MAP: {},
        SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_MAP: {},
      },
    });
    SettingsAPI.readCategory.mockResolvedValueOnce({
      data: {
        SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_CALLBACK_URL:
          'https://towerhost/sso/complete/github-enterprise-org/',
        SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_URL: 'https://localhost/url',
        SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_API_URL: 'https://localhost/apiurl',
        SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_KEY: 'ent_org_key',
        SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_SECRET: '$encrypted$',
        SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_NAME: 'ent_org_name',
        SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_ORGANIZATION_MAP: {},
        SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_TEAM_MAP: {},
      },
    });
    SettingsAPI.readCategory.mockResolvedValueOnce({
      data: {
        SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_CALLBACK_URL:
          'https://towerhost/sso/complete/github-enterprise-team/',
        SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_URL: 'https://localhost/url',
        SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_API_URL: 'https://localhost/apiurl',
        SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_KEY: 'ent_team_key',
        SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_SECRET: '$encrypted$',
        SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_ID: 'ent_team_id',
        SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_ORGANIZATION_MAP: {},
        SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_TEAM_MAP: {},
      },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should render github default details', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/github/'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <GitHub />
        </SettingsProvider>,
        {
          context: { router: { history } },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('GitHubDetail').length).toBe(1);
    expect(wrapper.find('Detail[label="GitHub OAuth2 Key"]').length).toBe(1);
  });

  test('should redirect to github organization category details', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/github/organization'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <GitHub />
        </SettingsProvider>,
        {
          context: { router: { history } },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('GitHubDetail').length).toBe(1);
    expect(
      wrapper.find('Detail[label="GitHub Organization OAuth2 Key"]').length
    ).toBe(1);
  });

  test('should render github edit', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/github/default/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <GitHub />
        </SettingsProvider>,
        {
          context: { router: { history } },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('GitHubEdit').length).toBe(1);
  });

  test('should show content error when user navigates to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/github/foo/bar'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <GitHub />
        </SettingsProvider>,
        {
          context: { router: { history } },
        }
      );
    });
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
