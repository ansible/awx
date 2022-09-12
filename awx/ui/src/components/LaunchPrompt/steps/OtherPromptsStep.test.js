import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import OtherPromptsStep from './OtherPromptsStep';

describe('OtherPromptsStep', () => {
  test('should render job type field', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik initialValues={{ job_type: 'run' }}>
          <OtherPromptsStep
            launchConfig={{
              ask_job_type_on_launch: true,
              job_template_data: {
                name: 'Demo Job Template',
                id: 1,
                description: '',
              },
            }}
          />
        </Formik>
      );
    });

    expect(wrapper.find('JobTypeField')).toHaveLength(1);
    expect(
      wrapper.find('JobTypeField AnsibleSelect').prop('data')
    ).toHaveLength(3);
    expect(wrapper.find('JobTypeField AnsibleSelect').prop('value')).toEqual(
      'run'
    );
  });

  test('should render limit field', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik>
          <OtherPromptsStep
            launchConfig={{
              ask_limit_on_launch: true,
              job_template_data: {
                name: 'Demo Job Template',
                id: 1,
                description: '',
              },
            }}
          />
        </Formik>
      );
    });

    expect(wrapper.find('FormField#prompt-limit')).toHaveLength(1);
    expect(wrapper.find('FormField#prompt-limit input').prop('name')).toEqual(
      'limit'
    );
  });

  test('should render source control branch field', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik>
          <OtherPromptsStep
            launchConfig={{
              ask_scm_branch_on_launch: true,
              job_template_data: {
                name: 'Demo Job Template',
                id: 1,
                description: '',
              },
            }}
          />
        </Formik>
      );
    });

    expect(wrapper.find('FormField#prompt-scm-branch')).toHaveLength(1);
    expect(
      wrapper.find('FormField#prompt-scm-branch input').prop('name')
    ).toEqual('scm_branch');
  });

  test('should render verbosity field', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik initialValues={{ verbosity: '' }}>
          <OtherPromptsStep
            launchConfig={{
              ask_verbosity_on_launch: true,
              job_template_data: {
                name: 'Demo Job Template',
                id: 1,
                description: '',
              },
            }}
          />
        </Formik>
      );
    });

    expect(wrapper.find('VerbosityField')).toHaveLength(1);
    expect(
      wrapper.find('VerbosityField AnsibleSelect').prop('data')
    ).toHaveLength(6);
  });

  test('should render show changes toggle', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik initialValues={{ diff_mode: true }}>
          <OtherPromptsStep
            launchConfig={{
              ask_diff_mode_on_launch: true,
              job_template_data: {
                name: 'Demo Job Template',
                id: 1,
                description: '',
              },
            }}
          />
        </Formik>
      );
    });

    expect(wrapper.find('ShowChangesToggle')).toHaveLength(1);
    expect(wrapper.find('ShowChangesToggle Switch').prop('isChecked')).toEqual(
      true
    );
  });

  test('should pass mode and onModeChange to VariablesField', async () => {
    let wrapper;
    const onModeChange = jest.fn();
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik initialValues={{ extra_vars: '{}' }}>
          <OtherPromptsStep
            variablesMode="javascript"
            onVarModeChange={onModeChange}
            launchConfig={{
              ask_variables_on_launch: true,
              job_template_data: {
                name: 'Demo Job Template',
                id: 1,
                description: '',
              },
            }}
          />
        </Formik>
      );
    });

    expect(wrapper.find('VariablesField').prop('initialMode')).toEqual(
      'javascript'
    );
    expect(wrapper.find('VariablesField').prop('onModeChange')).toEqual(
      onModeChange
    );
  });
});
