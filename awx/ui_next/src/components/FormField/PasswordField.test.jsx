import React from 'react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import { sleep } from '@testUtils/testUtils';
import { Formik } from 'formik';
import PasswordField from './PasswordField';

describe('PasswordField', () => {
  test('renders the expected content', () => {
    const wrapper = mountWithContexts(
      <Formik
        initialValues={{
          password: '',
        }}
        render={() => (
          <PasswordField id="test-password" name="password" label="Password" />
        )}
      />
    );
    expect(wrapper).toHaveLength(1);
  });

  test('properly responds to show/hide toggles', async () => {
    const wrapper = mountWithContexts(
      <Formik
        initialValues={{
          password: '',
        }}
        render={() => (
          <PasswordField id="test-password" name="password" label="Password" />
        )}
      />
    );
    expect(wrapper.find('input').prop('type')).toBe('password');
    expect(wrapper.find('EyeSlashIcon').length).toBe(1);
    expect(wrapper.find('EyeIcon').length).toBe(0);
    wrapper.find('button').simulate('click');
    await sleep(1);
    expect(wrapper.find('input').prop('type')).toBe('text');
    expect(wrapper.find('EyeSlashIcon').length).toBe(0);
    expect(wrapper.find('EyeIcon').length).toBe(1);
  });
});
