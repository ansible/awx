import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import { CredentialsAPI } from '../../api';
import AdHocCommandsWizard from './AdHocCommandsWizard';

jest.mock('../../api/models/CredentialTypes');
jest.mock('../../api/models/Inventories');
jest.mock('../../api/models/Credentials');

const adHocItems = [
  { name: 'Inventory 1' },
  { name: 'Inventory 2' },
  { name: 'inventory 3' },
];
describe('<AdHocCommandsWizard/>', () => {
  let wrapper;
  const onLaunch = jest.fn();
  beforeEach(async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <AdHocCommandsWizard
          adHocItems={adHocItems}
          onLaunch={onLaunch}
          moduleOptions={[]}
          verbosityOptions={[]}
          onCloseWizard={() => {}}
          credentialTypeId={1}
        />
      );
    });
  });
  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('should mount properly', async () => {
    // wrapper.update();
    expect(wrapper.find('AdHocCommandsWizard').length).toBe(1);
  });

  test('next and nav item should be disabled', async () => {
    // wrapper.update();
    await waitForElement(wrapper, 'WizardNavItem', el => el.length > 0);

    expect(
      wrapper.find('WizardNavItem[content="Details"]').prop('isCurrent')
    ).toBe(true);
    expect(
      wrapper.find('WizardNavItem[content="Details"]').prop('isDisabled')
    ).toBe(false);
    expect(
      wrapper
        .find('WizardNavItem[content="Machine Credential"]')
        .prop('isDisabled')
    ).toBe(true);
    expect(
      wrapper
        .find('WizardNavItem[content="Machine Credential"]')
        .prop('isCurrent')
    ).toBe(false);
    expect(wrapper.find('Button[type="submit"]').prop('isDisabled')).toBe(true);
  });

  test('next button should become active, and should navigate to the next step', async () => {
    await waitForElement(wrapper, 'WizardNavItem', el => el.length > 0);

    act(() => {
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
    wrapper.find('Button[type="submit"]').prop('onClick')();
    wrapper.update();
  });
  test('launch button should become active', async () => {
    CredentialsAPI.read.mockResolvedValue({
      data: {
        results: [
          { id: 1, name: 'Cred 1' },
          { id: 2, name: 'Cred2' },
        ],
        count: 2,
      },
    });
    await waitForElement(wrapper, 'WizardNavItem', el => el.length > 0);

    act(() => {
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
    wrapper.find('Button[type="submit"]').prop('onClick')();

    wrapper.update();
    await waitForElement(wrapper, 'OptionsList', el => el.length > 0);
    expect(wrapper.find('CheckboxListItem').length).toBe(2);
    expect(wrapper.find('Button[type="submit"]').prop('isDisabled')).toBe(true);

    await act(async () => {
      wrapper
        .find('input[aria-labelledby="check-action-item-1"]')
        .simulate('change', { target: { checked: true } });
    });

    wrapper.update();

    expect(
      wrapper.find('CheckboxListItem[label="Cred 1"]').prop('isSelected')
    ).toBe(true);
    expect(wrapper.find('Button[type="submit"]').prop('isDisabled')).toBe(
      false
    );
    wrapper.find('Button[type="submit"]').prop('onClick')();
    expect(onLaunch).toHaveBeenCalled();
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
    await waitForElement(wrapper, 'WizardNavItem', el => el.length > 0);

    act(() => {
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
    wrapper.find('Button[type="submit"]').prop('onClick')();

    wrapper.update();
    expect(wrapper.find('ContentLoading').length).toBe(1);
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
