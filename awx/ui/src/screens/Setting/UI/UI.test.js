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
import UI from './UI';

jest.mock('../../../api/models/Settings');
SettingsAPI.readCategory.mockResolvedValue({
  data: {
    CUSTOM_LOGIN_INFO: '',
    CUSTOM_LOGO: '',
    PENDO_TRACKING_STATE: 'off',
  },
});

describe('<UI />', () => {
  let wrapper;

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should render user interface details', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/ui/details'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <UI />
        </SettingsProvider>,
        {
          context: { router: { history } },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('UIDetail').length).toBe(1);
  });

  test('should render user interface edit', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/ui/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <UI />
        </SettingsProvider>,
        {
          context: { router: { history } },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('UIEdit').length).toBe(1);
  });

  test('should show content error when user navigates to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/ui/foo'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<UI />, {
        context: { router: { history } },
      });
    });
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
