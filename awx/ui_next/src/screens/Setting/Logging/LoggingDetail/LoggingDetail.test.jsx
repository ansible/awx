import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../../testUtils/enzymeHelpers';
import { SettingsProvider } from '../../../../contexts/Settings';
import { SettingsAPI } from '../../../../api';
import {
  assertDetail,
  assertVariableDetail,
} from '../../shared/settingTestUtils';
import mockAllOptions from '../../shared/data.allSettingOptions.json';
import mockLogSettings from '../../shared/data.logSettings.json';
import LoggingDetail from './LoggingDetail';

jest.mock('../../../../api/models/Settings');
SettingsAPI.readCategory.mockResolvedValue({
  data: mockLogSettings,
});

describe('<LoggingDetail />', () => {
  let wrapper;

  beforeAll(async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <LoggingDetail />
        </SettingsProvider>
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
  });

  afterAll(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('initially renders without crashing', () => {
    expect(wrapper.find('LoggingDetail').length).toBe(1);
  });

  test('should render expected tabs', () => {
    const expectedTabs = ['Back to Settings', 'Details'];
    wrapper.find('RoutedTabs li').forEach((tab, index) => {
      expect(tab.text()).toEqual(expectedTabs[index]);
    });
  });

  test('should render expected details', () => {
    assertDetail(wrapper, 'Enable External Logging', 'Off');
    assertDetail(wrapper, 'Logging Aggregator', 'https://mocklog');
    assertDetail(wrapper, 'Logging Aggregator Port', '1234');
    assertDetail(wrapper, 'Logging Aggregator Type', 'logstash');
    assertDetail(wrapper, 'Logging Aggregator Username', 'logging_name');
    assertDetail(wrapper, 'Logging Aggregator Password/Token', 'Encrypted');
    assertDetail(wrapper, 'Log System Tracking Facts Individually', 'Off');
    assertDetail(wrapper, 'Logging Aggregator Protocol', 'https');
    assertDetail(wrapper, 'TCP Connection Timeout', '5 seconds');
    assertDetail(wrapper, 'Logging Aggregator Level Threshold', 'INFO');
    assertDetail(
      wrapper,
      'Enable/disable HTTPS certificate verification',
      'On'
    );
    assertVariableDetail(
      wrapper,
      'Loggers Sending Data to Log Aggregator Form',
      '[\n  "activity_stream",\n  "system_tracking"\n]'
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
          <LoggingDetail />
        </SettingsProvider>,
        {
          context: { config },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('Button[aria-label="Edit"]').exists()).toBeFalsy();
  });

  test('should display content error when api throws error on initial render', async () => {
    SettingsAPI.readCategory.mockRejectedValue(new Error());
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <LoggingDetail />
        </SettingsProvider>
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
