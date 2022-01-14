import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { SettingsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import Logging from './Logging';

jest.mock('../../../api/models/Settings');
SettingsAPI.readCategory.mockResolvedValue({
  data: {
    LOG_AGGREGATOR_HOST: null,
    LOG_AGGREGATOR_PORT: null,
    LOG_AGGREGATOR_TYPE: null,
    LOG_AGGREGATOR_USERNAME: '',
    LOG_AGGREGATOR_PASSWORD: '',
    LOG_AGGREGATOR_LOGGERS: [
      'awx',
      'activity_stream',
      'job_events',
      'system_tracking',
    ],
    LOG_AGGREGATOR_INDIVIDUAL_FACTS: false,
    LOG_AGGREGATOR_ENABLED: false,
    LOG_AGGREGATOR_TOWER_UUID: '',
    LOG_AGGREGATOR_PROTOCOL: 'https',
    LOG_AGGREGATOR_TCP_TIMEOUT: 5,
    LOG_AGGREGATOR_VERIFY_CERT: true,
    LOG_AGGREGATOR_LEVEL: 'INFO',
    LOG_AGGREGATOR_MAX_DISK_USAGE_GB: 1,
    LOG_AGGREGATOR_MAX_DISK_USAGE_PATH: '/var/lib/awx',
    LOG_AGGREGATOR_RSYSLOGD_DEBUG: false,
    API_400_ERROR_LOG_FORMAT:
      'status {status_code} received by user {user_name} attempting to access {url_path} from {remote_addr}',
  },
});

describe('<Logging />', () => {
  let wrapper;

  afterEach(() => {
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
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
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
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
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

  test('should redirect to details for users without system admin permissions', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/logging/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<Logging />, {
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
    expect(wrapper.find('LoggingDetail').length).toBe(1);
    expect(wrapper.find('LoggingEdit').length).toBe(0);
  });
});
