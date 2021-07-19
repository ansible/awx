import React from 'react';
import { Formik } from 'formik';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import PasswordField from './PasswordField';

describe('PasswordField', () => {
  test('renders the expected content', () => {
    const wrapper = mountWithContexts(
      <Formik
        initialValues={{
          password: '',
        }}
      >
        {() => (
          <PasswordField id="test-password" name="password" label="Password" />
        )}
      </Formik>
    );
    expect(wrapper).toHaveLength(1);
  });
});
