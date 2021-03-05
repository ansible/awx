import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../../testUtils/enzymeHelpers';
import {
  ConfigAPI,
  MeAPI,
  SettingsAPI,
  RootAPI,
  UsersAPI,
} from '../../../../api';
import SubscriptionEdit from './SubscriptionEdit';

jest.mock('./bootstrapPendo');
jest.mock('../../../../api');
RootAPI.readAssetVariables.mockResolvedValue({
  data: {
    BRAND_NAME: 'Mock',
    PENDO_API_KEY: '',
  },
});

const mockConfig = {
  me: {
    is_superuser: true,
  },
  license_info: {
    compliant: true,
    current_instances: 1,
    date_expired: false,
    date_warning: true,
    free_instances: 1000,
    grace_period_remaining: 2904229,
    instance_count: 1001,
    license_date: '1614401999',
    license_type: 'enterprise',
    pool_id: '123',
    product_name: 'Red Hat Ansible Automation, Standard (5000 Managed Nodes)',
    satellite: false,
    sku: 'ABC',
    subscription_name:
      'Red Hat Ansible Automation, Standard (1001 Managed Nodes)',
    support_level: null,
    time_remaining: 312229,
    trial: false,
    valid_key: true,
  },
  analytics_status: 'detailed',
  version: '1.2.3',
};

const emptyConfig = {
  me: {
    is_superuser: true,
  },
  license_info: {
    valid_key: false,
  },
};

describe('<SubscriptionEdit />', () => {
  describe('installing a fresh subscription', () => {
    let wrapper;
    let history;

    beforeAll(async () => {
      SettingsAPI.readCategory.mockResolvedValue({
        data: {},
      });
      history = createMemoryHistory({
        initialEntries: ['/settings/subscription_managment'],
      });
      await act(async () => {
        wrapper = mountWithContexts(<SubscriptionEdit />, {
          context: {
            config: emptyConfig,
            router: { history },
          },
        });
      });
      await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    });

    afterAll(() => {
      jest.clearAllMocks();
      wrapper.unmount();
    });

    test('initially renders without crashing', () => {
      expect(wrapper.find('SubscriptionEdit').length).toBe(1);
    });

    test('should show all wizard steps when it is a trial or a fresh installation', () => {
      expect(
        wrapper.find('WizardNavItem[content="Mock Subscription"]').length
      ).toBe(1);
      expect(
        wrapper.find('WizardNavItem[content="User and Insights analytics"]')
          .length
      ).toBe(1);
      expect(
        wrapper.find('WizardNavItem[content="End user license agreement"]')
          .length
      ).toBe(1);
      expect(
        wrapper.find('button[aria-label="Cancel subscription edit"]').length
      ).toBe(0);
    });

    test('subscription selection type toggle should default to manifest', () => {
      expect(
        wrapper
          .find('ToggleGroupItem')
          .first()
          .text()
      ).toBe('Subscription manifest');
      expect(
        wrapper
          .find('ToggleGroupItem')
          .first()
          .props().isSelected
      ).toBe(true);
      expect(
        wrapper
          .find('ToggleGroupItem')
          .last()
          .text()
      ).toBe('Username / password');
      expect(
        wrapper
          .find('ToggleGroupItem')
          .last()
          .props().isSelected
      ).toBe(false);
    });

    test('file upload field should upload manifest file', async () => {
      expect(wrapper.find('FileUploadField').prop('filename')).toEqual('');
      const mockFile = new Blob(['123'], { type: 'application/zip' });
      mockFile.name = 'mock.zip';
      mockFile.date = new Date();
      await act(async () => {
        wrapper.find('FileUpload').invoke('onChange')(mockFile, 'mock.zip');
      });
      await act(async () => {
        wrapper.update();
      });
      await act(async () => {
        wrapper.update();
      });
      expect(wrapper.find('FileUploadField').prop('filename')).toEqual(
        'mock.zip'
      );
    });

    test('clicking next button should show analytics step', async () => {
      await act(async () => {
        wrapper.find('Button[children="Next"]').simulate('click');
      });
      wrapper.update();
      expect(wrapper.find('AnalyticsStep').length).toBe(1);
      expect(wrapper.find('CheckboxField').length).toBe(2);
      expect(wrapper.find('FormField').length).toBe(1);
      expect(wrapper.find('PasswordField').length).toBe(1);
    });

    test('deselecting insights checkbox should hide username and password fields', async () => {
      expect(wrapper.find('input#username-field')).toHaveLength(1);
      expect(wrapper.find('input#password-field')).toHaveLength(1);
      await act(async () => {
        wrapper.find('Checkbox[name="pendo"] input').simulate('change', {
          target: { value: false, name: 'pendo' },
        });
        wrapper.find('Checkbox[name="insights"] input').simulate('change', {
          target: { value: false, name: 'insights' },
        });
      });
      wrapper.update();
      expect(wrapper.find('input#username-field')).toHaveLength(0);
      expect(wrapper.find('input#password-field')).toHaveLength(0);
    });

    test('clicking next button should show eula step', async () => {
      await act(async () => {
        wrapper.find('Button[children="Next"]').simulate('click');
      });
      wrapper.update();
      expect(wrapper.find('EulaStep').length).toBe(1);
      expect(wrapper.find('CheckboxField').length).toBe(1);
      expect(wrapper.find('Button[children="Submit"]').length).toBe(1);
    });

    test('checking EULA agreement should enable Submit button', async () => {
      expect(wrapper.find('Button[children="Submit"]').prop('isDisabled')).toBe(
        true
      );
      await act(async () => {
        wrapper.find('Checkbox[name="eula"] input').simulate('change', {
          target: { value: true, name: 'eula' },
        });
      });
      wrapper.update();
      expect(wrapper.find('Button[children="Submit"]').prop('isDisabled')).toBe(
        false
      );
    });

    test('should successfully save on form submission', async () => {
      const { window } = global;
      global.window.pendo = { initialize: jest.fn().mockResolvedValue({}) };
      ConfigAPI.read.mockResolvedValue({
        data: mockConfig,
      });
      MeAPI.read.mockResolvedValue({
        data: {
          results: [
            {
              is_superuser: true,
            },
          ],
        },
      });
      ConfigAPI.attach.mockResolvedValue({});
      ConfigAPI.create.mockResolvedValue({
        data: mockConfig,
      });
      UsersAPI.readAdminOfOrganizations({
        data: {},
      });
      expect(wrapper.find('Alert[title="Save successful"]')).toHaveLength(0);
      await act(async () =>
        wrapper.find('button[aria-label="Submit"]').simulate('click')
      );
      wrapper.update();
      waitForElement(wrapper, 'Alert[title="Save successful"]');
      global.window = window;
    });
  });

  describe('editing with a valid subscription', () => {
    let wrapper;
    let history;

    beforeAll(async () => {
      SettingsAPI.readCategory.mockResolvedValue({
        data: {
          SUBSCRIPTIONS_PASSWORD: 'mock_password',
          SUBSCRIPTIONS_USERNAME: 'mock_username',
          INSIGHTS_TRACKING_STATE: false,
          PENDO: 'off',
        },
      });
      ConfigAPI.readSubscriptions.mockResolvedValue({
        data: [
          {
            subscription_name: 'mock subscription 50 instances',
            instance_count: 50,
            license_date: new Date(),
            pool_id: 999,
          },
        ],
      });
      history = createMemoryHistory({
        initialEntries: ['/settings/subscription/edit'],
      });
      await act(async () => {
        wrapper = mountWithContexts(<SubscriptionEdit />, {
          context: {
            config: {
              mockConfig,
            },
            me: {
              is_superuser: true,
            },
            router: { history },
          },
        });
      });
      await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    });

    afterAll(() => {
      jest.clearAllMocks();
      wrapper.unmount();
    });

    test('should hide analytics step when editing a current subscription', async () => {
      expect(
        wrapper.find('WizardNavItem[content="Subscription Management"]').length
      ).toBe(1);
      expect(
        wrapper.find('WizardNavItem[content="User and Insights analytics"]')
          .length
      ).toBe(0);
      expect(
        wrapper.find('WizardNavItem[content="End user license agreement"]')
          .length
      ).toBe(1);
    });

    test('Username/password toggle button should show username credential fields', async () => {
      expect(
        wrapper
          .find('ToggleGroupItem')
          .last()
          .props().isSelected
      ).toBe(false);
      wrapper
        .find('ToggleGroupItem[text="Username / password"] button')
        .simulate('click');
      wrapper.update();
      expect(
        wrapper
          .find('ToggleGroupItem')
          .last()
          .props().isSelected
      ).toBe(true);
      expect(wrapper.find('input#username-field').prop('value')).toEqual('');
      expect(wrapper.find('input#password-field').prop('value')).toEqual('');
      await act(async () => {
        wrapper.find('input#username-field').simulate('change', {
          target: { value: 'username-cred', name: 'username' },
        });
        wrapper.find('input#password-field').simulate('change', {
          target: { value: 'password-cred', name: 'password' },
        });
      });
      wrapper.update();
      expect(wrapper.find('input#username-field').prop('value')).toEqual(
        'username-cred'
      );
      expect(wrapper.find('input#password-field').prop('value')).toEqual(
        'password-cred'
      );
    });

    test('should open subscription selection modal', async () => {
      expect(wrapper.find('Flex[id="selected-subscription-file"]').length).toBe(
        0
      );
      await act(async () => {
        wrapper
          .find('SubscriptionStep button[aria-label="Get subscriptions"]')
          .simulate('click');
      });
      wrapper.update();
      await waitForElement(wrapper, 'SubscriptionModal');
      await act(async () => {
        wrapper
          .find('SubscriptionModal SelectColumn')
          .first()
          .invoke('onSelect')();
      });
      wrapper.update();
      await act(async () =>
        wrapper.find('Button[aria-label="Confirm selection"]').prop('onClick')()
      );
      wrapper.update();
      await waitForElement(wrapper, 'SubscriptionModal', el => el.length === 0);
    });

    test('should show selected subscription name', () => {
      expect(wrapper.find('Flex[id="selected-subscription"]').length).toBe(1);
      expect(wrapper.find('Flex[id="selected-subscription"] i').text()).toBe(
        'mock subscription 50 instances'
      );
    });
    test('next should skip analytics step and navigate to eula step', async () => {
      await act(async () => {
        wrapper.find('Button[children="Next"]').simulate('click');
      });
      wrapper.update();
      expect(wrapper.find('SubscriptionStep').length).toBe(0);
      expect(wrapper.find('AnalyticsStep').length).toBe(0);
      expect(wrapper.find('EulaStep').length).toBe(1);
    });

    test('submit should be disabled until EULA agreement checked', async () => {
      expect(wrapper.find('Button[children="Submit"]').prop('isDisabled')).toBe(
        true
      );
      await act(async () => {
        wrapper.find('Checkbox[name="eula"] input').simulate('change', {
          target: { value: true, name: 'eula' },
        });
      });
      wrapper.update();
      expect(wrapper.find('Button[children="Submit"]').prop('isDisabled')).toBe(
        false
      );
    });

    test('should successfully send request to api on form submission', async () => {
      expect(wrapper.find('EulaStep').length).toBe(1);
      ConfigAPI.read.mockResolvedValue({
        data: {
          mockConfig,
        },
      });
      MeAPI.read.mockResolvedValue({
        data: {
          results: [
            {
              is_superuser: true,
            },
          ],
        },
      });
      ConfigAPI.attach.mockResolvedValue({});
      ConfigAPI.create.mockResolvedValue({});
      UsersAPI.readAdminOfOrganizations({
        data: {},
      });
      waitForElement(
        wrapper,
        'Alert[title="Save successful"]',
        el => el.length === 0
      );
      await act(async () =>
        wrapper.find('Button[children="Submit"]').prop('onClick')()
      );
      wrapper.update();
      waitForElement(wrapper, 'Alert[title="Save successful"]');
    });

    test('should navigate to subscription details on cancel', async () => {
      expect(
        wrapper.find('button[aria-label="Cancel subscription edit"]').length
      ).toBe(1);
      await act(async () => {
        wrapper
          .find('button[aria-label="Cancel subscription edit"]')
          .invoke('onClick')();
      });
      expect(history.location.pathname).toEqual(
        '/settings/subscription/details'
      );
    });
  });

  test.only('should throw a content error', async () => {
    RootAPI.readAssetVariables.mockRejectedValueOnce(new Error());
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<SubscriptionEdit />, {
        context: {
          config: emptyConfig,
        },
      });
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
    jest.clearAllMocks();
    wrapper.unmount();
  });
});
