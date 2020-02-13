import React from 'react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import { Field, Formik } from 'formik';
import FieldWithPrompt from './FieldWithPrompt';

describe('FieldWithPrompt', () => {
  let wrapper;

  afterEach(() => {
    wrapper.unmount();
  });

  test('Required asterisk and Tooltip hidden when not required and tooltip not provided', () => {
    wrapper = mountWithContexts(
      <Formik
        initialValues={{
          ask_limit_on_launch: false,
          limit: '',
        }}
      >
        {() => (
          <FieldWithPrompt
            fieldId="job-template-limit"
            label="Limit"
            promptId="job-template-ask-limit-on-launch"
            promptName="ask_limit_on_launch"
          >
            <Field name="limit">
              {() => <input id="job-template-limit" type="text" />}
            </Field>
          </FieldWithPrompt>
        )}
      </Formik>
    );
    expect(wrapper.find('.pf-c-form__label-required')).toHaveLength(0);
    expect(wrapper.find('Tooltip')).toHaveLength(0);
  });

  test('Required asterisk and Tooltip shown when required and tooltip provided', () => {
    wrapper = mountWithContexts(
      <Formik
        initialValues={{
          ask_limit_on_launch: false,
          limit: '',
        }}
      >
        {() => (
          <FieldWithPrompt
            fieldId="job-template-limit"
            label="Limit"
            promptId="job-template-ask-limit-on-launch"
            promptName="ask_limit_on_launch"
            tooltip="Help text"
            isRequired
          >
            <Field name="limit">
              {() => <input id="job-template-limit" type="text" />}
            </Field>
          </FieldWithPrompt>
        )}
      </Formik>
    );
    expect(wrapper.find('.pf-c-form__label-required')).toHaveLength(1);
    expect(wrapper.find('Tooltip')).toHaveLength(1);
  });
});
