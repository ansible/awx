import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { SettingsProvider } from 'contexts/Settings';
import { SettingsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../../testUtils/enzymeHelpers';
import mockAllOptions from '../../shared/data.allSettingOptions.json';
import LoggingEdit from './LoggingEdit';

jest.mock('../../../../api');

const mockSettings = {
  LOG_AGGREGATOR_HOST: 'https://logstash',
  LOG_AGGREGATOR_PORT: 1234,
  LOG_AGGREGATOR_TYPE: 'logstash',
  LOG_AGGREGATOR_USERNAME: '',
  LOG_AGGREGATOR_PASSWORD: '',
  LOG_AGGREGATOR_LOGGERS: [
    'awx',
    'activity_stream',
    'job_events',
    'system_tracking',
  ],
  LOG_AGGREGATOR_INDIVIDUAL_FACTS: false,
  LOG_AGGREGATOR_ENABLED: true,
  LOG_AGGREGATOR_TOWER_UUID: '',
  LOG_AGGREGATOR_PROTOCOL: 'https',
  LOG_AGGREGATOR_TCP_TIMEOUT: 123,
  LOG_AGGREGATOR_VERIFY_CERT: true,
  LOG_AGGREGATOR_LEVEL: 'ERROR',
  LOG_AGGREGATOR_MAX_DISK_USAGE_GB: 1,
  LOG_AGGREGATOR_MAX_DISK_USAGE_PATH: '/var/lib/awx',
  LOG_AGGREGATOR_RSYSLOGD_DEBUG: false,
  API_400_ERROR_LOG_FORMAT:
    'status {status_code} received by user {user_name} attempting to access {url_path} from {remote_addr}',
};

describe('<LoggingEdit />', () => {
  let wrapper;
  let history;

  afterEach(() => {
    jest.clearAllMocks();
  });

  beforeEach(async () => {
    SettingsAPI.revertCategory.mockResolvedValue({});
    SettingsAPI.updateAll.mockResolvedValue({});
    SettingsAPI.readCategory.mockResolvedValue({
      data: mockSettings,
    });
    history = createMemoryHistory({
      initialEntries: ['/settings/logging/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <LoggingEdit />
        </SettingsProvider>,
        {
          context: { router: { history } },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
  });

  test('initially renders without crashing', () => {
    expect(wrapper.find('LoggingEdit').length).toBe(1);
  });

  test('Enable External Logging toggle should be disabled when it is off and there is no Logging Aggregator or no Logging Aggregator Type', async () => {
    const enableLoggingField =
      "FormGroup[label='Enable External Logging'] Switch";
    const loggingAggregatorField =
      "FormGroup[label='Logging Aggregator'] TextInputBase";
    expect(wrapper.find(enableLoggingField).prop('isChecked')).toBe(true);
    expect(wrapper.find(enableLoggingField).prop('isDisabled')).toBe(false);
    await act(async () => {
      wrapper.find(enableLoggingField).invoke('onChange')(false);
    });
    await act(async () => {
      wrapper.find(loggingAggregatorField).invoke('onChange')(null, {
        target: {
          name: 'LOG_AGGREGATOR_HOST',
          value: '',
        },
      });
    });
    wrapper.update();
    expect(
      wrapper.find(enableLoggingField).find('Switch').prop('isChecked')
    ).toBe(false);
    expect(
      wrapper.find(enableLoggingField).find('Switch').prop('isDisabled')
    ).toBe(true);
  });

  test('Logging Aggregator and Logging Aggregator Type should be required when External Logging toggle is enabled', () => {
    const enableLoggingField = wrapper.find(
      "FormGroup[label='Enable External Logging']"
    );
    const loggingAggregatorField = wrapper.find(
      "FormGroup[label='Logging Aggregator']"
    );
    const loggingAggregatorTypeField = wrapper.find(
      "FormGroup[label='Logging Aggregator Type']"
    );
    expect(enableLoggingField.find('RevertButton').text()).toEqual('Revert');
    expect(
      loggingAggregatorField.find('.pf-c-form__label-required')
    ).toHaveLength(1);
    expect(
      loggingAggregatorTypeField.find('.pf-c-form__label-required')
    ).toHaveLength(1);
  });

  test('Logging Aggregator and Logging Aggregator Type should not be required when External Logging toggle is disabled', async () => {
    await act(async () => {
      wrapper
        .find("FormGroup[label='Enable External Logging'] Switch")
        .invoke('onChange')(false);
    });
    wrapper.update();
    const enableLoggingField = wrapper.find(
      "FormGroup[label='Enable External Logging']"
    );
    const loggingAggregatorField = wrapper.find(
      "FormGroup[label='Logging Aggregator']"
    );
    const loggingAggregatorTypeField = wrapper.find(
      "FormGroup[label='Logging Aggregator Type']"
    );
    expect(enableLoggingField.find('RevertButton').text()).toEqual('Undo');
    expect(
      loggingAggregatorField.find('.pf-c-form__label-required')
    ).toHaveLength(0);
    expect(
      loggingAggregatorTypeField.find('.pf-c-form__label-required')
    ).toHaveLength(0);
  });

  test('HTTPS certificate toggle should be shown when protocol is https', () => {
    const httpsField = wrapper.find(
      "FormGroup[label='Enable/disable HTTPS certificate verification']"
    );
    expect(httpsField).toHaveLength(1);
    expect(httpsField.find('Switch').prop('isChecked')).toBe(true);
  });

  test('TCP connection timeout should be required when protocol is tcp', () => {
    const tcpTimeoutField = wrapper.find(
      "FormGroup[label='TCP Connection Timeout']"
    );
    expect(tcpTimeoutField).toHaveLength(1);
    expect(tcpTimeoutField.find('.pf-c-form__label-required')).toHaveLength(1);
  });

  test('TCP connection timeout and https certificate toggle should be hidden when protocol is udp', async () => {
    await act(async () => {
      wrapper
        .find('AnsibleSelect[name="LOG_AGGREGATOR_PROTOCOL"]')
        .invoke('onChange')({
        target: {
          name: 'LOG_AGGREGATOR_PROTOCOL',
          value: 'udp',
        },
      });
    });
    wrapper.update();
    expect(
      wrapper.find(
        "FormGroup[label='Enable/disable HTTPS certificate verification']"
      )
    ).toHaveLength(0);
    expect(
      wrapper.find("FormGroup[label='TCP Connection Timeout']")
    ).toHaveLength(0);
    expect(
      wrapper.find("FormGroup[label='Logging Aggregator Level Threshold']")
    ).toHaveLength(1);
  });

  test('should successfully send default values to api on form revert all', async () => {
    expect(SettingsAPI.revertCategory).toHaveBeenCalledTimes(0);
    expect(wrapper.find('RevertAllAlert')).toHaveLength(0);
    await act(async () => {
      wrapper
        .find('button[aria-label="Revert all to default"]')
        .invoke('onClick')();
    });
    wrapper.update();
    expect(wrapper.find('RevertAllAlert')).toHaveLength(1);
    await act(async () => {
      wrapper
        .find('RevertAllAlert button[aria-label="Confirm revert all"]')
        .invoke('onClick')();
    });
    wrapper.update();
    expect(SettingsAPI.revertCategory).toHaveBeenCalledTimes(1);
    expect(SettingsAPI.revertCategory).toHaveBeenCalledWith('logging');
  });

  test('should successfully send request to api on form submission', async () => {
    expect(SettingsAPI.updateAll).toHaveBeenCalledTimes(0);
    const loggingAggregatorField =
      "FormGroup[label='Logging Aggregator'] TextInputBase";
    await act(async () => {
      wrapper.find(loggingAggregatorField).invoke('onChange')(null, {
        target: {
          name: 'LOG_AGGREGATOR_PORT',
          value: 1010,
        },
      });
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('Form').invoke('onSubmit')();
    });
    expect(SettingsAPI.updateAll).toHaveBeenCalledTimes(1);
    expect(SettingsAPI.updateAll).toHaveBeenCalledWith({
      ...mockSettings,
      LOG_AGGREGATOR_PORT: 1010,
    });
  });

  test('should navigate to logging detail on successful submission', async () => {
    await act(async () => {
      wrapper.find('Form').invoke('onSubmit')();
    });
    expect(history.location.pathname).toEqual('/settings/logging/details');
  });

  test('should navigate to logging detail when cancel is clicked', async () => {
    await act(async () => {
      wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    });
    expect(history.location.pathname).toEqual('/settings/logging/details');
  });

  test('should display error message on unsuccessful submission', async () => {
    const error = {
      response: {
        data: { detail: 'An error occurred' },
      },
    };
    SettingsAPI.updateAll.mockImplementation(() => Promise.reject(error));
    expect(wrapper.find('FormSubmitError').length).toBe(0);
    expect(SettingsAPI.updateAll).toHaveBeenCalledTimes(0);
    await act(async () => {
      wrapper.find('Form').invoke('onSubmit')();
    });
    wrapper.update();
    expect(wrapper.find('FormSubmitError').length).toBe(1);
    expect(SettingsAPI.updateAll).toHaveBeenCalledTimes(1);
  });

  test('should display ContentError on throw', async () => {
    SettingsAPI.readCategory.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <LoggingEdit />
        </SettingsProvider>
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
