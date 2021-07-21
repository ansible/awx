import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { SettingsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import MiscAuthentication from './MiscAuthentication';

jest.mock('../../../api');

describe('<MiscAuthentication />', () => {
  let wrapper;

  beforeEach(() => {
    SettingsAPI.readCategory.mockResolvedValue({
      data: {},
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should render miscellaneous authentication details', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/miscellaneous_authentication/details'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<MiscAuthentication />, {
        context: { router: { history } },
      });
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('MiscAuthenticationDetail').length).toBe(1);
  });

  test('should render miscellaneous authentication edit', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/miscellaneous_authentication/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<MiscAuthentication />, {
        context: { router: { history } },
      });
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('MiscAuthenticationEdit').length).toBe(1);
  });

  test('should show content error when user navigates to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/miscellaneous_authentication/foo'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<MiscAuthentication />, {
        context: { router: { history } },
      });
    });
    expect(wrapper.find('ContentError').length).toBe(1);
  });

  test('should redirect to details for users without system admin permissions', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/miscellaneous_authentication/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<MiscAuthentication />, {
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
    expect(wrapper.find('MiscAuthenticationDetail').length).toBe(1);
    expect(wrapper.find('MiscAuthenticationEdit').length).toBe(0);
  });
});
