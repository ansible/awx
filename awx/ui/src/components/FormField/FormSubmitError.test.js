import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import FormSubmitError from './FormSubmitError';

describe('<FormSubmitError>', () => {
  test('should render null when no error present', async () => {
    const wrapper = mountWithContexts(
      <Formik>{() => <FormSubmitError error={null} />}</Formik>
    );
    const ele = await wrapper.find('FormSubmitError').text();
    expect(ele).toEqual('');
  });

  test('should pass field errors to Formik', async () => {
    const error = {
      response: {
        data: {
          name: 'invalid',
        },
      },
    };
    const wrapper = mountWithContexts(
      <Formik initialValues={{ name: '' }}>
        {({ errors }) => (
          <div>
            <p>{errors.name}</p>
            <FormSubmitError error={error} />
          </div>
        )}
      </Formik>
    );
    const pp = await wrapper.find('p').text();
    expect(pp).toEqual('invalid');
  });
});
