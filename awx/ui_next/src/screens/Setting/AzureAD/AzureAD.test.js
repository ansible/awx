import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { SettingsProvider } from 'contexts/Settings';
import { SettingsAPI } from 'api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import mockAllOptions from '../shared/data.allSettingOptions.json';
import AzureAD from './AzureAD';

jest.mock('../../../api');

describe('<AzureAD />', () => {
  let wrapper;

  beforeEach(() => {
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
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should render azure details', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/azure/details'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <AzureAD />
        </SettingsProvider>,
        {
          context: { router: { history } },
        }
      );
    });
    expect(wrapper.find('AzureADDetail').length).toBe(1);
  });

  test('should render azure edit', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/azure/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<AzureAD />, {
        context: { router: { history } },
      });
    });
    expect(wrapper.find('AzureADEdit').length).toBe(1);
  });

  test('should show content error when user navigates to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/azure/foo'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<AzureAD />, {
        context: { router: { history } },
      });
    });
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
