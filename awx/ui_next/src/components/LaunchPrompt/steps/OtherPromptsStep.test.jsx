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
            config={{
              ask_job_type_on_launch: true,
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
            config={{
              ask_limit_on_launch: true,
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
            config={{
              ask_scm_branch_on_launch: true,
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
            config={{
              ask_verbosity_on_launch: true,
            }}
          />
        </Formik>
      );
    });

    expect(wrapper.find('VerbosityField')).toHaveLength(1);
    expect(
      wrapper.find('VerbosityField AnsibleSelect').prop('data')
    ).toHaveLength(5);
  });

  test('should render show changes toggle', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik initialValues={{ diff_mode: true }}>
          <OtherPromptsStep
            config={{
              ask_diff_mode_on_launch: true,
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
});
