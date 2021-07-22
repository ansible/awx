import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import FormSubmitError from './FormSubmitError';

describe('<FormSubmitError>', () => {
  test('should render null when no error present', () => {
    const wrapper = mountWithContexts(
      <Formik>{() => <FormSubmitError error={null} />}</Formik>
    );
    expect(wrapper.find('FormSubmitError').text()).toEqual('');
  });

  test('should pass field errors to Formik', () => {
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
    expect(wrapper.find('p').text()).toEqual('invalid');
  });

  test('should display error message if field errors not provided', async () => {
    const realConsole = global.console;
    global.console = {
      error: jest.fn(),
    };
    const error = {
      message: 'There was an error',
    };
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik>{() => <FormSubmitError error={error} />}</Formik>
      );
    });
    wrapper.update();
    expect(wrapper.find('Alert').prop('title')).toEqual('There was an error');
    expect(global.console.error).toHaveBeenCalledWith(error);
    global.console = realConsole;
  });
});
