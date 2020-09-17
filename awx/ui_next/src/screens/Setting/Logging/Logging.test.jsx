import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import { SettingsAPI } from '../../../api';
import Logging from './Logging';

jest.mock('../../../api/models/Settings');
SettingsAPI.readCategory.mockResolvedValue({
  data: {},
});

describe('<Logging />', () => {
  let wrapper;

  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('should render logging details', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/logging/details'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<Logging />, {
        context: { router: { history } },
      });
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('LoggingDetail').length).toBe(1);
  });

  test('should render logging edit', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/logging/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<Logging />, {
        context: { router: { history } },
      });
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('LoggingEdit').length).toBe(1);
  });

  test('should show content error when user navigates to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/logging/foo'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<Logging />, {
        context: { router: { history } },
      });
    });
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
