import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { SettingsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import MiscSystem from './MiscSystem';

jest.mock('../../../api');

describe('<MiscSystem />', () => {
  let wrapper;

  beforeEach(() => {
    SettingsAPI.readCategory.mockResolvedValue({
      data: {},
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should render miscellaneous system details', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/miscellaneous_system/details'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<MiscSystem />, {
        context: { router: { history } },
      });
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('MiscSystemDetail').length).toBe(1);
  });

  test('should render miscellaneous system edit', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/miscellaneous_system/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<MiscSystem />, {
        context: { router: { history } },
      });
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('MiscSystemEdit').length).toBe(1);
  });

  test('should show content error when user navigates to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/miscellaneous_system/foo'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<MiscSystem />, {
        context: { router: { history } },
      });
    });
    expect(wrapper.find('ContentError').length).toBe(1);
  });

  test('should redirect to details for users without system admin permissions', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/miscellaneous_system/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<MiscSystem />, {
        context: {
          router: {
            history,
          },
          config: {
            me: {
              is_superuser: false,
            },
          },
        },
      });
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('MiscSystemDetail').length).toBe(1);
    expect(wrapper.find('MiscSystemEdit').length).toBe(0);
  });
});
