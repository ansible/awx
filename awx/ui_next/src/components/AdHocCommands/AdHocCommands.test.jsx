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

const children = ({ openAdHocCommands }) => (
  <button type="submit" onClick={() => openAdHocCommands()} />
);

describe('<AdHocCOmmands />', () => {
  let wrapper;
  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('mounts successfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <AdHocCommands
          apiModule={InventoriesAPI}
          adHocItems={adHocItems}
          itemId={1}
          credentialTypeId={1}
        >
          {children}
        </AdHocCommands>
      );
    });
    expect(wrapper.find('AdHocCommands').length).toBe(1);
  });
  test('calls api on Mount', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <AdHocCommands
          apiModule={InventoriesAPI}
          adHocItems={adHocItems}
          itemId={1}
          credentialTypeId={1}
        >
          {children}
        </AdHocCommands>
      );
    });
    expect(wrapper.find('AdHocCommands').length).toBe(1);
    expect(InventoriesAPI.readAdHocOptions).toBeCalledWith(1);
    expect(CredentialTypesAPI.read).toBeCalledWith({ namespace: 'ssh' });
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
        <AdHocCommands
          apiModule={InventoriesAPI}
          adHocItems={adHocItems}
          itemId={1}
          credentialTypeId={1}
        >
          {children}
        </AdHocCommands>
      );
    });
    await act(async () => wrapper.find('button').prop('onClick')());

    wrapper.update();

    expect(wrapper.find('AdHocCommandsWizard').length).toBe(1);
  });

  test('should submit properly', async () => {
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
    InventoriesAPI.launchAdHocCommands.mockResolvedValue({ data: { id: 1 } });
    await act(async () => {
      wrapper = mountWithContexts(
        <AdHocCommands
          apiModule={InventoriesAPI}
          adHocItems={adHocItems}
          itemId={1}
          credentialTypeId={1}
        >
          {children}
        </AdHocCommands>
      );
    });
    await act(async () => wrapper.find('button').prop('onClick')());

    wrapper.update();

    expect(wrapper.find('Button[type="submit"]').prop('isDisabled')).toBe(true);

    expect(
      wrapper
        .find('WizardNavItem[content="Machine credential"]')
        .prop('isDisabled')
    ).toBe(true);

    await act(async () => {
      wrapper.find('AnsibleSelect[name="module_args"]').prop('onChange')(
        {},
        'command'
      );
      wrapper.find('input#arguments').simulate('change', {
        target: { value: 'foo', name: 'arguments' },
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
      arguments: 'foo',
      changes: false,
      credential: 4,
      escalation: false,
      extra_vars: '---',
      forks: 0,
      limit: 'Inventory 1 Org 0, Inventory 2 Org 0',
      module_args: 'command',
      verbosity: 1,
    });

    wrapper.update();

    expect(wrapper.find('AdHocCommandsWizard').length).toBe(0);
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
        <AdHocCommands
          apiModule={InventoriesAPI}
          adHocItems={adHocItems}
          itemId={1}
          credentialTypeId={1}
        >
          {children}
        </AdHocCommands>
      );
    });
    await act(async () => wrapper.find('button').prop('onClick')());

    wrapper.update();

    expect(wrapper.find('Button[type="submit"]').prop('isDisabled')).toBe(true);
    expect(
      wrapper
        .find('WizardNavItem[content="Machine credential"]')
        .prop('isDisabled')
    ).toBe(true);

    await act(async () => {
      wrapper.find('AnsibleSelect[name="module_args"]').prop('onChange')(
        {},
        'command'
      );
      wrapper.find('input#arguments').simulate('change', {
        target: { value: 'foo', name: 'arguments' },
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

    wrapper.update();

    expect(wrapper.find('AdHocCommandsWizard').length).toBe(0);
    expect(wrapper.find('ErrorDetail').length).toBe(1);
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
        <AdHocCommands
          apiModule={InventoriesAPI}
          adHocItems={adHocItems}
          itemId={1}
          credentialTypeId={1}
        >
          {children}
        </AdHocCommands>
      );
    });
    await act(async () => wrapper.find('button').prop('onClick')());
    wrapper.update();
    expect(wrapper.find('ErrorDetail').length).toBe(1);
  });
});
