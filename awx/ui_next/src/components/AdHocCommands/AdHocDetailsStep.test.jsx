import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import DetailsStep from './AdHocDetailsStep';

jest.mock('../../api/models/Credentials');

const verbosityOptions = [
  { key: -1, value: '', label: '', isDisabled: false },
  { key: 0, value: 0, label: '0', isDisabled: false },
  { key: 1, value: 1, label: '1', isDisabled: false },
];
const moduleOptions = [
  ['command', 'command'],
  ['shell', 'shell'],
];
const onLimitChange = jest.fn();
const initialValues = {
  limit: ['Inventory 1', 'inventory 2'],
  credential: [],
  module_args: '',
  arguments: '',
  verbosity: '',
  forks: 0,
  changes: false,
  escalation: false,
  extra_vars: '---',
  module_name: 'shell',
};

describe('<AdHocDetailsStep />', () => {
  let wrapper;

  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('should mount properly', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik initialValues={initialValues}>
          <DetailsStep
            verbosityOptions={verbosityOptions}
            moduleOptions={moduleOptions}
            onLimitChange={onLimitChange}
          />
        </Formik>
      );
    });
  });

  test('should show all the fields', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik initialValues={initialValues}>
          <DetailsStep
            verbosityOptions={verbosityOptions}
            moduleOptions={moduleOptions}
            onLimitChange={onLimitChange}
          />
        </Formik>
      );
    });
    expect(wrapper.find('FormGroup[label="Module"]').length).toBe(1);
    expect(wrapper.find('FormField[label="Arguments"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Verbosity"]').length).toBe(1);
    expect(wrapper.find('FormField[label="Limit"]').length).toBe(1);
    expect(wrapper.find('FormField[name="forks"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Show changes"]').length).toBe(1);
    expect(wrapper.find('FormGroup[name="become_enabled"]').length).toBe(1);
    expect(wrapper.find('VariablesField').length).toBe(1);
  });

  test('shold update form values', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik initialValues={initialValues}>
          <DetailsStep
            verbosityOptions={verbosityOptions}
            moduleOptions={moduleOptions}
            onLimitChange={onLimitChange}
          />
        </Formik>
      );
    });

    await act(async () => {
      wrapper.find('AnsibleSelect[name="module_name"]').prop('onChange')(
        {},
        'command'
      );
      wrapper.find('input#module_args').simulate('change', {
        target: { value: 'foo', name: 'module_args' },
      });
      wrapper.find('input#limit').simulate('change', {
        target: {
          value: 'Inventory 1, inventory 2, new inventory',
          name: 'limit',
        },
      });
      wrapper.find('AnsibleSelect[name="verbosity"]').prop('onChange')({}, 1);

      wrapper.find('TextInputBase[name="forks"]').simulate('change', {
        target: { value: 10, name: 'forks' },
      });
      wrapper.find('Switch').invoke('onChange')();
      wrapper
        .find('Checkbox[aria-label="Enable privilege escalation"]')
        .invoke('onChange')(true, {
        currentTarget: { value: true, type: 'change', checked: true },
      });
    });
    wrapper.update();
    expect(
      wrapper.find('AnsibleSelect[name="module_name"]').prop('value')
    ).toBe('command');
    expect(wrapper.find('input#module_args').prop('value')).toBe('foo');
    expect(wrapper.find('AnsibleSelect[name="verbosity"]').prop('value')).toBe(
      1
    );
    expect(wrapper.find('TextInputBase[name="forks"]').prop('value')).toBe(10);
    expect(wrapper.find('TextInputBase[name="limit"]').prop('value')).toBe(
      'Inventory 1, inventory 2, new inventory'
    );
    expect(wrapper.find('Switch').prop('isChecked')).toBe(true);
    expect(
      wrapper
        .find('Checkbox[aria-label="Enable privilege escalation"]')
        .prop('isChecked')
    ).toBe(true);
  });
});
