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
          />
        </Formik>
      );
    });

    const detail = wrapper.find('PromptDetail');
    expect(detail).toHaveLength(1);
    expect(detail.prop('resource')).toEqual(resource);
    expect(detail.prop('overrides')).toEqual({
      extra_vars: '---',
      limit: '4',
    });
  });
});
