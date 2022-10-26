import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { SettingsProvider } from 'contexts/Settings';
import { SettingsAPI } from 'api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import mockAllOptions from '../shared/data.allSettingOptions.json';
import TACACS from './TACACS';

jest.mock('../../../api/models/Settings');
SettingsAPI.readCategory.mockResolvedValue({
  data: {
    TACACSPLUS_HOST: 'mockhost',
    TACACSPLUS_PORT: 49,
    TACACSPLUS_SECRET: '$encrypted$',
    TACACSPLUS_SESSION_TIMEOUT: 5,
    TACACSPLUS_AUTH_PROTOCOL: 'ascii',
    TACACSPLUS_REM_ADDR: false,
  },
});

describe('<TACACS />', () => {
  let wrapper;

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should render TACACS+ details', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/tacacs/details'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <TACACS />
        </SettingsProvider>,
        {
          context: { router: { history } },
        }
      );
    });
    expect(wrapper.find('TACACSDetail').length).toBe(1);
  });

  test('should render TACACS+ edit', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/tacacs/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <TACACS />
        </SettingsProvider>,
        {
          context: { router: { history } },
        }
      );
    });
    expect(wrapper.find('TACACSEdit').length).toBe(1);
  });

  test('should show content error when user navigates to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/tacacs/foo'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<TACACS />, {
        context: { router: { history } },
      });
    });
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
