import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { SettingsProvider } from 'contexts/Settings';
import { SettingsAPI, ExecutionEnvironmentsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../../testUtils/enzymeHelpers';
import mockAllOptions from '../../shared/data.allSettingOptions.json';
import mockAllSettings from '../../shared/data.allSettings.json';
import MiscSystemEdit from './MiscSystemEdit';

jest.mock('../../../../api');

const mockExecutionEnvironment = [
  {
    id: 1,
    name: 'Default EE',
    description: '',
    image: 'quay.io/ansible/awx-ee',
  },
];

const systemData = {
  ACTIVITY_STREAM_ENABLED: true,
  ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC: false,
  AUTOMATION_ANALYTICS_GATHER_INTERVAL: 14400,
  AUTOMATION_ANALYTICS_LAST_ENTRIES: '',
  AUTOMATION_ANALYTICS_URL: 'https://example.com',
  DEFAULT_EXECUTION_ENVIRONMENT: 1,
  INSIGHTS_TRACKING_STATE: false,
  MANAGE_ORGANIZATION_AUTH: true,
  ORG_ADMINS_CAN_SEE_ALL_USERS: true,
  REDHAT_USERNAME: '',
  REDHAT_PASSWORD: '',
  SUBSCRIPTIONS_USERNAME: '',
  SUBSCRIPTIONS_PASSWORD: '',
  REMOTE_HOST_HEADERS: ['REMOTE_ADDR', 'REMOTE_HOST'],
  TOWER_URL_BASE: 'https://localhost:3000',
  PROXY_IP_ALLOWED_LIST: [],
  CSRF_TRUSTED_ORIGINS: [],
  UI_NEXT: false,
};

describe('<MiscSystemEdit />', () => {
  let wrapper;
  let history;

  afterEach(() => {
    jest.clearAllMocks();
  });

  beforeEach(async () => {
    SettingsAPI.revertCategory.mockResolvedValue({});
    SettingsAPI.updateAll.mockResolvedValue({});
    SettingsAPI.readCategory.mockResolvedValue({
      data: mockAllSettings,
    });
    ExecutionEnvironmentsAPI.read.mockResolvedValue({
      data: {
        results: mockExecutionEnvironment,
        count: 1,
      },
    });
    history = createMemoryHistory({
      initialEntries: ['/settings/miscellaneous_system/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <MiscSystemEdit />
        </SettingsProvider>,
        {
          context: { router: { history } },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
  });

  test('initially renders without crashing', async () => {
    expect(wrapper.find('MiscSystemEdit').length).toBe(1);
  });

  test('save button should call updateAll', async () => {
    expect(wrapper.find('MiscSystemEdit').length).toBe(1);

    wrapper.find('ExecutionEnvironmentLookup').invoke('onChange')({
      id: 1,
      name: 'Foo',
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('button[aria-label="Save"]').simulate('click');
    });
    wrapper.update();
    expect(SettingsAPI.updateAll).toHaveBeenCalledWith(systemData);
  });

  test('should remove execution environment', async () => {
    expect(wrapper.find('MiscSystemEdit').length).toBe(1);

    wrapper.find('ExecutionEnvironmentLookup').invoke('onChange')(null);
    wrapper.update();
    await act(async () => {
      wrapper.find('button[aria-label="Save"]').simulate('click');
    });

    expect(SettingsAPI.updateAll).toHaveBeenCalledWith({
      ...systemData,
      DEFAULT_EXECUTION_ENVIRONMENT: null,
    });
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
    expect(SettingsAPI.revertCategory).toHaveBeenCalledWith('system');
  });

  test('should successfully send request to api on form submission', async () => {
    await act(async () => {
      wrapper.find('Form').invoke('onSubmit')();
    });
    expect(SettingsAPI.updateAll).toHaveBeenCalledTimes(1);
  });

  test('should navigate to miscellaneous detail on successful submission', async () => {
    await act(async () => {
      wrapper.find('Form').invoke('onSubmit')();
    });
    expect(history.location.pathname).toEqual(
      '/settings/miscellaneous_system/details'
    );
  });

  test('should navigate to miscellaneous detail when cancel is clicked', async () => {
    await act(async () => {
      wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    });
    expect(history.location.pathname).toEqual(
      '/settings/miscellaneous_system/details'
    );
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
          <MiscSystemEdit />
        </SettingsProvider>
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
