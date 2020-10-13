import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import PreviewStep from './PreviewStep';

const resource = {
  id: 1,
  type: 'job_template',
  summary_fields: {
    inventory: { id: 12 },
    recent_jobs: [],
  },
  related: {},
};

const survey = {
  name: '',
  spec: [
    {
      variable: 'foo',
      type: 'text',
    },
  ],
};

const formErrors = {
  inventory: 'An inventory must be selected',
};

describe('PreviewStep', () => {
  test('should render PromptDetail', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik initialValues={{ limit: '4', survey_foo: 'abc' }}>
          <PreviewStep
            resource={resource}
            config={{
              ask_limit_on_launch: true,
              survey_enabled: true,
            }}
            survey={survey}
            formErrors={formErrors}
          />
        </Formik>
      );
    });

    const detail = wrapper.find('PromptDetail');
    expect(detail).toHaveLength(1);
    expect(detail.prop('resource')).toEqual(resource);
    expect(detail.prop('overrides')).toEqual({
      extra_vars: 'foo: abc\n',
      limit: '4',
      survey_foo: 'abc',
    });
  });

  test('should render PromptDetail without survey', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik initialValues={{ limit: '4' }}>
          <PreviewStep
            resource={resource}
            config={{
              ask_limit_on_launch: true,
            }}
            formErrors={formErrors}
          />
        </Formik>
      );
    });

    const detail = wrapper.find('PromptDetail');
    expect(detail).toHaveLength(1);
    expect(detail.prop('resource')).toEqual(resource);
    expect(detail.prop('overrides')).toEqual({
      limit: '4',
    });
  });

  test('should handle extra vars without survey', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik initialValues={{ extra_vars: 'one: 1' }}>
          <PreviewStep
            resource={resource}
            config={{
              ask_variables_on_launch: true,
            }}
            formErrors={formErrors}
          />
        </Formik>
      );
    });

    const detail = wrapper.find('PromptDetail');
    expect(detail).toHaveLength(1);
    expect(detail.prop('resource')).toEqual(resource);
    expect(detail.prop('overrides')).toEqual({
      extra_vars: 'one: 1',
    });
  });

  test('should remove survey with empty array value', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik
          initialValues={{ extra_vars: 'one: 1' }}
          values={{ extra_vars: 'one: 1', survey_foo: [] }}
        >
          <PreviewStep
            resource={resource}
            config={{
              ask_variables_on_launch: true,
            }}
            formErrors={formErrors}
          />
        </Formik>
      );
    });

    const detail = wrapper.find('PromptDetail');
    expect(detail).toHaveLength(1);
    expect(detail.prop('resource')).toEqual(resource);
    expect(detail.prop('overrides')).toEqual({
      extra_vars: 'one: 1',
    });
  });
});
