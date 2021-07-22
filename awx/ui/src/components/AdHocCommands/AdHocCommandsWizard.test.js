import React from 'react';
import { act } from 'react-dom/test-utils';
import { CredentialsAPI, ExecutionEnvironmentsAPI, RootAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import AdHocCommandsWizard from './AdHocCommandsWizard';

jest.mock('../../api/models/CredentialTypes');
jest.mock('../../api/models/Inventories');
jest.mock('../../api/models/Credentials');
jest.mock('../../api/models/ExecutionEnvironments');
jest.mock('../../api/models/Root');

const verbosityOptions = [
  { value: '0', key: '0', label: '0 (Normal)' },
  { value: '1', key: '1', label: '1 (Verbose)' },
  { value: '2', key: '2', label: '2 (More Verbose)' },
  { value: '3', key: '3', label: '3 (Debug)' },
  { value: '4', key: '4', label: '4 (Connection Debug)' },
];
const moduleOptions = [
  ['command', 'command'],
  ['shell', 'shell'],
];
const adHocItems = [
  { name: 'Inventory 1' },
  { name: 'Inventory 2' },
  { name: 'inventory 3' },
];
describe('<AdHocCommandsWizard/>', () => {
  let wrapper;
  const onLaunch = jest.fn();
  beforeEach(async () => {
    RootAPI.readAssetVariables.mockResolvedValue({
      data: {
        BRAND_NAME: 'AWX',
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <AdHocCommandsWizard
          adHocItems={adHocItems}
          onLaunch={onLaunch}
          moduleOptions={moduleOptions}
          verbosityOptions={verbosityOptions}
          onCloseWizard={() => {}}
          credentialTypeId={1}
          organizationId={1}
        />
      );
    });
  });
  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should mount properly', async () => {
    expect(wrapper.find('AdHocCommandsWizard').length).toBe(1);
  });

  test('launch button should be disabled', async () => {
    waitForElement(wrapper, 'WizardNavItem', (el) => el.length > 0);

    expect(wrapper.find('Button[type="submit"]').prop('isDisabled')).toBe(
      false
    );
    act(() => wrapper.find('Button[type="submit"]').prop('onClick')());
    expect(wrapper.find('Button[type="submit"]').prop('isDisabled')).toBe(
      false
    );
    wrapper.update();
    act(() => wrapper.find('Button[type="submit"]').prop('onClick')());
    expect(wrapper.find('Button[type="submit"]').prop('isDisabled')).toBe(
      false
    );
    wrapper.update();
    act(() => wrapper.find('Button[type="submit"]').prop('onClick')());
    wrapper.update();

    expect(wrapper.find('AdHocPreviewStep').prop('hasErrors')).toBe(true);
    expect(wrapper.find('Button[type="submit"]').prop('isDisabled')).toBe(true);
  });

  test('launch button should become active', async () => {
    ExecutionEnvironmentsAPI.read.mockResolvedValue({
      data: {
        results: [
          { id: 1, name: 'EE 1', url: '' },
          { id: 2, name: 'EE 2', url: '' },
        ],
        count: 2,
      },
    });
    ExecutionEnvironmentsAPI.readOptions.mockResolvedValue({
      data: { actions: { GET: {} } },
    });
    CredentialsAPI.read.mockResolvedValue({
      data: {
        results: [
          { id: 1, name: 'Cred 1', url: '' },
          { id: 2, name: 'Cred2', url: '' },
        ],
        count: 2,
      },
    });
    CredentialsAPI.readOptions.mockResolvedValue({
      data: { actions: { GET: {} } },
    });
    await waitForElement(wrapper, 'WizardNavItem', (el) => el.length > 0);

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

    wrapper.update();

    // step 2

    await waitForElement(wrapper, 'OptionsList', (el) => el.length > 0);
    expect(wrapper.find('CheckboxListItem').length).toBe(2);
    expect(wrapper.find('Button[type="submit"]').prop('isDisabled')).toBe(
      false
    );

    await act(async () => {
      wrapper.find('td#check-action-item-1').find('input').simulate('click');
    });

    wrapper.update();

    expect(
      wrapper.find('CheckboxListItem[label="EE 1"]').prop('isSelected')
    ).toBe(true);
    expect(wrapper.find('Button[type="submit"]').prop('isDisabled')).toBe(
      false
    );

    await act(async () =>
      wrapper.find('Button[type="submit"]').prop('onClick')()
    );

    wrapper.update();
    // step 3

    await waitForElement(wrapper, 'OptionsList', (el) => el.length > 0);
    expect(wrapper.find('CheckboxListItem').length).toBe(2);

    await act(async () => {
      wrapper.find('td#check-action-item-1').find('input').simulate('click');
    });

    wrapper.update();

    expect(
      wrapper.find('CheckboxListItem[label="Cred 1"]').prop('isSelected')
    ).toBe(true);

    await act(async () =>
      wrapper.find('Button[type="submit"]').prop('onClick')()
    );
    wrapper.update();
    await act(async () =>
      wrapper.find('Button[type="submit"]').prop('onClick')()
    );
    expect(wrapper.find('Button[type="submit"]').prop('isDisabled')).toBe(
      false
    );

    expect(onLaunch).toHaveBeenCalledWith({
      become_enabled: '',
      credential: [{ id: 1, name: 'Cred 1', url: '' }],
      diff_mode: false,
      execution_environment: [{ id: 1, name: 'EE 1', url: '' }],
      extra_vars: '---',
      forks: 0,
      job_type: 'run',
      limit: 'Inventory 1, Inventory 2, inventory 3',
      module_args: 'foo',
      module_name: 'command',
      verbosity: 1,
    });
  });

  test('should show error in navigation bar', async () => {
    await waitForElement(wrapper, 'WizardNavItem', (el) => el.length > 0);

    await act(async () => {
      wrapper.find('AnsibleSelect[name="module_name"]').prop('onChange')(
        {},
        'command'
      );
      wrapper.find('input#module_args').simulate('change', {
        target: { value: '', name: 'module_args' },
      });
    });
    waitForElement(wrapper, 'ExclamationCircleIcon', (el) => el.length > 0);
  });

  test('expect credential step to throw error', async () => {
    CredentialsAPI.read.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'get',
            url: '/api/v2/credentals',
          },
          data: 'An error occurred',
          status: 403,
        },
      })
    );
    CredentialsAPI.readOptions.mockResolvedValue({
      data: { actions: { GET: {} } },
    });
    await waitForElement(wrapper, 'WizardNavItem', (el) => el.length > 0);

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

    wrapper.update();

    await act(async () =>
      wrapper.find('Button[type="submit"]').prop('onClick')()
    );

    wrapper.update();
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
