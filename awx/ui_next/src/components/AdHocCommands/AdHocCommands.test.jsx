import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import { CredentialTypesAPI, InventoriesAPI, CredentialsAPI } from '../../api';
import AdHocCommands from './AdHocCommands';

jest.mock('../../api/models/CredentialTypes');
jest.mock('../../api/models/Inventories');
jest.mock('../../api/models/Credentials');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({
    id: 1,
  }),
}));
const credentials = [
  { id: 1, kind: 'cloud', name: 'Cred 1', url: 'www.google.com' },
  { id: 2, kind: 'ssh', name: 'Cred 2', url: 'www.google.com' },
  { id: 3, kind: 'Ansible', name: 'Cred 3', url: 'www.google.com' },
  { id: 4, kind: 'Machine', name: 'Cred 4', url: 'www.google.com' },
  { id: 5, kind: 'Machine', name: 'Cred 5', url: 'www.google.com' },
];

const adHocItems = [
  {
    name: 'Inventory 1 Org 0',
  },
  { name: 'Inventory 2 Org 0' },
];

describe('<AdHocCommands />', () => {
  beforeEach(() => {
    InventoriesAPI.readAdHocOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {
            module_name: {
              choices: [
                ['command', 'command'],
                ['shell', 'shell'],
              ],
            },
          },
          POST: {},
        },
      },
    });
    CredentialTypesAPI.read.mockResolvedValue({
      data: { count: 1, results: [{ id: 1, name: 'cred' }] },
    });
  });
  let wrapper;
  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('mounts successfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <AdHocCommands adHocItems={adHocItems} hasListItems />
      );
    });
    expect(wrapper.find('AdHocCommands').length).toBe(1);
  });

  test('should open the wizard', async () => {
    InventoriesAPI.readAdHocOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {
            module_name: {
              choices: [
                ['command', 'command'],
                ['foo', 'foo'],
              ],
            },
            verbosity: { choices: [[1], [2]] },
          },
        },
      },
    });
    CredentialTypesAPI.read.mockResolvedValue({
      data: { results: [{ id: 1 }] },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <AdHocCommands adHocItems={adHocItems} hasListItems />
      );
    });
    await act(async () =>
      wrapper.find('button[aria-label="Run Command"]').prop('onClick')()
    );

    wrapper.update();

    expect(wrapper.find('AdHocCommandsWizard').length).toBe(1);
  });

  test('should submit properly', async () => {
    InventoriesAPI.launchAdHocCommands.mockResolvedValue({ data: { id: 1 } });
    CredentialsAPI.read.mockResolvedValue({
      data: {
        results: credentials,
        count: 5,
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <AdHocCommands adHocItems={adHocItems} hasListItems />
      );
    });

    await act(async () =>
      wrapper.find('button[aria-label="Run Command"]').prop('onClick')()
    );
    wrapper.update();

    expect(wrapper.find('Button[type="submit"]').prop('isDisabled')).toBe(true);

    expect(
      wrapper
        .find('WizardNavItem[content="Machine credential"]')
        .prop('isDisabled')
    ).toBe(true);

    await act(async () => {
      wrapper.find('AnsibleSelect[name="module_name"]').prop('onChange')(
        {},
        'command'
      );
      wrapper.find('input#module_args').simulate('change', {
        target: { value: 'foo', name: 'module_args' },
      });
      wrapper.find('AnsibleSelect[name="verbosity"]').prop('onChange')({}, 1);
    });

    wrapper.update();

    expect(wrapper.find('Button[type="submit"]').prop('isDisabled')).toBe(
      false
    );
    await act(async () =>
      wrapper.find('Button[type="submit"]').prop('onClick')()
    );
    await waitForElement(wrapper, 'ContentEmpty', el => el.length === 0);
    // second step of wizard

    await act(async () => {
      wrapper
        .find('input[aria-labelledby="check-action-item-4"]')
        .simulate('change', { target: { checked: true } });
    });

    wrapper.update();

    expect(
      wrapper.find('CheckboxListItem[label="Cred 4"]').prop('isSelected')
    ).toBe(true);

    await act(async () =>
      wrapper.find('Button[type="submit"]').prop('onClick')()
    );

    expect(InventoriesAPI.launchAdHocCommands).toBeCalledWith(1, {
      module_args: 'foo',
      diff_mode: false,
      credential: 4,
      job_type: 'run',
      become_enabled: '',
      extra_vars: '---',
      forks: 0,
      limit: 'Inventory 1 Org 0, Inventory 2 Org 0',
      module_name: 'command',
      verbosity: 1,
    });
  });

  test('should throw error on submission properly', async () => {
    InventoriesAPI.launchAdHocCommands.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'post',
            url: '/api/v2/inventories/1/ad_hoc_commands',
          },
          data: 'An error occurred',
          status: 403,
        },
      })
    );
    InventoriesAPI.readAdHocOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {
            module_name: {
              choices: [
                ['command', 'command'],
                ['foo', 'foo'],
              ],
            },
            verbosity: { choices: [[1], [2]] },
          },
        },
      },
    });
    CredentialTypesAPI.read.mockResolvedValue({
      data: { results: [{ id: 1 }] },
    });
    CredentialsAPI.read.mockResolvedValue({
      data: {
        results: credentials,
        count: 5,
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <AdHocCommands adHocItems={adHocItems} hasListItems />
      );
    });

    await act(async () =>
      wrapper.find('button[aria-label="Run Command"]').prop('onClick')()
    );
    wrapper.update();

    expect(wrapper.find('Button[type="submit"]').prop('isDisabled')).toBe(true);
    expect(
      wrapper
        .find('WizardNavItem[content="Machine credential"]')
        .prop('isDisabled')
    ).toBe(true);

    await act(async () => {
      wrapper.find('AnsibleSelect[name="module_name"]').prop('onChange')(
        {},
        'command'
      );
      wrapper.find('input#module_args').simulate('change', {
        target: { value: 'foo', name: 'module_args' },
      });
      wrapper.find('AnsibleSelect[name="verbosity"]').prop('onChange')({}, 1);
    });

    wrapper.update();

    expect(wrapper.find('Button[type="submit"]').prop('isDisabled')).toBe(
      false
    );

    await act(async () =>
      wrapper.find('Button[type="submit"]').prop('onClick')()
    );

    await waitForElement(wrapper, 'ContentEmpty', el => el.length === 0);

    // second step of wizard

    await act(async () => {
      wrapper
        .find('input[aria-labelledby="check-action-item-4"]')
        .simulate('change', { target: { checked: true } });
    });

    wrapper.update();

    expect(
      wrapper.find('CheckboxListItem[label="Cred 4"]').prop('isSelected')
    ).toBe(true);

    await act(async () =>
      wrapper.find('Button[type="submit"]').prop('onClick')()
    );

    await waitForElement(wrapper, 'ErrorDetail', el => el.length > 0);
  });

  test('should disable run command button due to permissions', async () => {
    InventoriesAPI.readHosts.mockResolvedValue({
      data: { results: [], count: 0 },
    });
    InventoriesAPI.readAdHocOptions.mockResolvedValue({
      data: {
        actions: {
          GET: { module_name: { choices: [['module']] } },
        },
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <AdHocCommands adHocItems={adHocItems} hasListItems />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    const runCommandsButton = wrapper.find('button[aria-label="Run Command"]');
    expect(runCommandsButton.prop('disabled')).toBe(true);
  });

  test('should disable run command button due to lack of list items', async () => {
    InventoriesAPI.readHosts.mockResolvedValue({
      data: { results: [], count: 0 },
    });
    InventoriesAPI.readAdHocOptions.mockResolvedValue({
      data: {
        actions: {
          GET: { module_name: { choices: [['module']] } },
        },
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <AdHocCommands adHocItems={adHocItems} hasListItems={false} />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    const runCommandsButton = wrapper.find('button[aria-label="Run Command"]');
    expect(runCommandsButton.prop('disabled')).toBe(true);
  });

  test('should open alert modal when error on fetching data', async () => {
    InventoriesAPI.readAdHocOptions.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'options',
            url: '/api/v2/inventories/1/',
          },
          data: 'An error occurred',
          status: 403,
        },
      })
    );
    await act(async () => {
      wrapper = mountWithContexts(
        <AdHocCommands adHocItems={adHocItems} hasListItems />
      );
    });
    await act(async () => wrapper.find('button').prop('onClick')());
    wrapper.update();
    expect(wrapper.find('ErrorDetail').length).toBe(1);
  });
});
