import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { SettingsProvider } from 'contexts/Settings';
import { SettingsAPI } from 'api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import mockAllOptions from '../shared/data.allSettingOptions.json';
import OIDC from './OIDC';

jest.mock('../../../api');

describe('<OIDC />', () => {
  let wrapper;

  beforeEach(() => {
    SettingsAPI.readCategory.mockResolvedValue({
      data: {
        SOCIAL_AUTH_OIDC_KEY: 'mock key',
        SOCIAL_AUTH_OIDC_SECRET: '$encrypted$',
        SOCIAL_AUTH_OIDC_OIDC_ENDPOINT: 'https://example.com',
        SOCIAL_AUTH_OIDC_VERIFY_SSL: true,
      },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should render OIDC details', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/oidc/details'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <OIDC />
        </SettingsProvider>,
        {
          context: { router: { history } },
        }
      );
    });
    expect(wrapper.find('OIDCDetail').length).toBe(1);
  });

  test('should render OIDC edit', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/oidc/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <OIDC />
        </SettingsProvider>,
        {
          context: { router: { history } },
        }
      );
    });
    expect(wrapper.find('OIDCEdit').length).toBe(1);
  });

  test('should show content error when user navigates to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/oidc/foo'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<OIDC />, {
        context: { router: { history } },
      });
    });
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
