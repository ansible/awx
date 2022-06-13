import React from 'react';
import { act } from 'react-dom/test-utils';
import { SettingsProvider } from 'contexts/Settings';
import { SettingsAPI, ExecutionEnvironmentsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../../testUtils/enzymeHelpers';
import {
  assertDetail,
  assertVariableDetail,
} from '../../shared/settingTestUtils';
import mockAllOptions from '../../shared/data.allSettingOptions.json';
import MiscSystemDetail from './MiscSystemDetail';

jest.mock('../../../../api');

describe('<MiscSystemDetail />', () => {
  let wrapper;

  beforeEach(async () => {
    SettingsAPI.readCategory = jest.fn();
    SettingsAPI.readCategory.mockResolvedValue({
      data: {
        ACTIVITY_STREAM_ENABLED: true,
        ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC: false,
        ORG_ADMINS_CAN_SEE_ALL_USERS: true,
        MANAGE_ORGANIZATION_AUTH: true,
        TOWER_URL_BASE: 'https://towerhost',
        REMOTE_HOST_HEADERS: [],
        PROXY_IP_ALLOWED_LIST: [],
        LICENSE: null,
        REDHAT_USERNAME: 'name1',
        REDHAT_PASSWORD: '$encrypted$',
        SUBSCRIPTIONS_USERNAME: 'name2',
        SUBSCRIPTIONS_PASSWORD: '$encrypted$',
        AUTOMATION_ANALYTICS_URL: 'https://example.com',
        INSTALL_UUID: 'db39b9ec-0c6e-4554-987d-42aw9c732ed8',
        DEFAULT_EXECUTION_ENVIRONMENT: 1,
        CUSTOM_VENV_PATHS: [],
        INSIGHTS_TRACKING_STATE: false,
        AUTOMATION_ANALYTICS_LAST_GATHER: null,
        AUTOMATION_ANALYTICS_LAST_ENTRIES:
          '{"foo": "2021-11-24R06:35:15.179Z"}',
        AUTOMATION_ANALYTICS_GATHER_INTERVAL: 14400,
      },
    });
    ExecutionEnvironmentsAPI.readDetail = jest.fn();
    ExecutionEnvironmentsAPI.readDetail.mockResolvedValue({
      data: {
        id: 1,
        name: 'Foo',
        image: 'quay.io/ansible/awx-ee',
        pull: 'missing',
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <MiscSystemDetail />
        </SettingsProvider>
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
  });

  test('initially renders without crashing', () => {
    expect(wrapper.find('MiscSystemDetail').length).toBe(1);
  });

  test('should render expected tabs', () => {
    const expectedTabs = ['Back to Settings', 'Details'];
    wrapper.find('RoutedTabs li').forEach((tab, index) => {
      expect(tab.text()).toEqual(expectedTabs[index]);
    });
  });

  test('should render expected details', () => {
    assertDetail(
      wrapper,
      'Unique identifier for an installation',
      'db39b9ec-0c6e-4554-987d-42aw9c732ed8'
    );
    assertDetail(wrapper, 'All Users Visible to Organization Admins', 'On');
    assertDetail(
      wrapper,
      'Automation Analytics Gather Interval',
      '14400 seconds'
    );
    assertDetail(
      wrapper,
      'Automation Analytics upload URL',
      'https://example.com'
    );
    assertDetail(wrapper, 'Base URL of the service', 'https://towerhost');
    assertDetail(wrapper, 'Gather data for Automation Analytics', 'Off');
    assertDetail(
      wrapper,
      'Organization Admins Can Manage Users and Teams',
      'On'
    );
    assertDetail(wrapper, 'Enable Activity Stream', 'On');
    assertDetail(wrapper, 'Enable Activity Stream for Inventory Sync', 'Off');
    assertDetail(wrapper, 'Red Hat customer password', 'Encrypted');
    assertDetail(wrapper, 'Red Hat customer username', 'name1');
    assertDetail(wrapper, 'Red Hat or Satellite password', 'Encrypted');
    assertDetail(wrapper, 'Red Hat or Satellite username', 'name2');
    assertVariableDetail(
      wrapper,
      'Last gathered entries from the data collection service of Automation Analytics',
      '{\n  "foo": "2021-11-24R06:35:15.179Z"\n}'
    );
    assertVariableDetail(wrapper, 'Remote Host Headers', '[]');
    assertVariableDetail(wrapper, 'Proxy IP Allowed List', '[]');
    assertDetail(wrapper, 'Global default execution environment', 'Foo');
  });

  test('should render execution environment as not configured', async () => {
    ExecutionEnvironmentsAPI.readDetail.mockResolvedValue({
      data: {},
    });
    let newWrapper;
    await act(async () => {
      newWrapper = mountWithContexts(
        <SettingsProvider
          value={{
            ...mockAllOptions.actions,
            DEFAULT_EXECUTION_ENVIRONMENT: null,
          }}
        >
          <MiscSystemDetail />
        </SettingsProvider>
      );
    });
    await waitForElement(newWrapper, 'ContentLoading', (el) => el.length === 0);

    assertDetail(
      newWrapper,
      'Global default execution environment',
      'Not configured'
    );
  });

  test('should hide edit button from non-superusers', async () => {
    const config = {
      me: {
        is_superuser: false,
      },
    };
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <MiscSystemDetail />
        </SettingsProvider>,
        {
          context: { config },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('Button[aria-label="Edit"]').exists()).toBeFalsy();
  });

  test('should display content error when api throws error on initial render', async () => {
    SettingsAPI.readCategory.mockRejectedValue(new Error());
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <MiscSystemDetail />
        </SettingsProvider>
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
