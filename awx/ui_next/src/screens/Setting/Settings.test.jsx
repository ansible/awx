import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import { SettingsAPI } from '../../api';
import mockAllOptions from './shared/data.allSettingOptions.json';
import Settings from './Settings';

jest.mock('../../api/models/Settings');
SettingsAPI.readAllOptions.mockResolvedValue({
  data: mockAllOptions,
});
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
}));

describe('<Settings />', () => {
  let wrapper;

  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('should render Redirect for users without system admin or auditor permissions', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<Settings />, {
        context: {
          router: {
            history,
          },
          config: {
            me: {
              is_superuser: false,
              is_system_auditor: false,
            },
          },
        },
      });
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('Redirect').length).toBe(1);
    expect(wrapper.find('SettingList').length).toBe(0);
  });

  test('should render Settings for users with system admin or auditor permissions', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<Settings />, {
        context: {
          router: {
            history,
          },
          config: {
            is_superuser: true,
            is_system_auditor: true,
          },
        },
      });
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('SettingList').length).toBe(1);
  });

  test('should render content error on throw', async () => {
    SettingsAPI.readAllOptions.mockRejectedValue(new Error());
    await act(async () => {
      wrapper = mountWithContexts(<Settings />);
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
