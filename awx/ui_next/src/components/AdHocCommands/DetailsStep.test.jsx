import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import DetailsStep from './DetailsStep';

jest.mock('../../api/models/Credentials');

const verbosityOptions = [
  { key: -1, value: '', label: '', isDisabled: false },
  { key: 0, value: 0, label: '0', isDisabled: false },
  { key: 1, value: 1, label: '1', isDisabled: false },
];
const moduleOptions = [
  { key: -1, value: '', label: '', isDisabled: false },
  { key: 0, value: 'command', label: 'command', isDisabled: false },
  { key: 1, value: 'shell', label: 'shell', isDisabled: false },
];
const onLimitChange = jest.fn();
const limitValue = '';
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
};

describe('<DetailsStep />', () => {
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
            limitValue={limitValue}
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
            limitValue={limitValue}
          />
        </Formik>
      );
    });
    expect(wrapper.find('FormGroup[label="Module"]').length).toBe(1);
    expect(wrapper.find('FormField[name="arguments"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Verbosity"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Limit"]').length).toBe(1);
    expect(wrapper.find('FormField[name="forks"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Show changes"]').length).toBe(1);
    expect(
      wrapper.find('FormGroup[name="enable privilege escalation"]').length
    ).toBe(1);
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
            limitValue={limitValue}
          />
        </Formik>
      );
    });

    await act(async () => {
      wrapper.find('AnsibleSelect[name="module_args"]').prop('onChange')(
        {},
        'command'
      );
      wrapper.find('input#arguments').simulate('change', {
        target: { value: 'foo', name: 'arguments' },
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
      wrapper.find('AnsibleSelect[name="module_args"]').prop('value')
    ).toBe('command');
    expect(wrapper.find('input#arguments').prop('value')).toBe('foo');
    expect(wrapper.find('AnsibleSelect[name="verbosity"]').prop('value')).toBe(
      1
    );
    expect(wrapper.find('TextInputBase[name="forks"]').prop('value')).toBe(10);
    expect(wrapper.find('TextInputBase[label="Limit"]').prop('value')).toBe('');
    expect(wrapper.find('Switch').prop('isChecked')).toBe(true);
    expect(
      wrapper
        .find('Checkbox[aria-label="Enable privilege escalation"]')
        .prop('isChecked')
    ).toBe(true);
  });

  test('should mount with proper limit value', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik initialValues={initialValues}>
          <DetailsStep
            verbosityOptions={verbosityOptions}
            moduleOptions={moduleOptions}
            onLimitChange={onLimitChange}
            limitValue="foo value"
          />
        </Formik>
      );
    });
    expect(wrapper.find('TextInputBase[label="Limit"]').prop('value')).toBe(
      'foo value'
    );
  });
});
