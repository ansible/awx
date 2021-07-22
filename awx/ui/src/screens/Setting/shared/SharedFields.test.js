import React from 'react';
import { Formik } from 'formik';
import { I18nProvider } from '@lingui/react';
import { act } from 'react-dom/test-utils';
import { i18n } from '@lingui/core';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import {
  BooleanField,
  ChoiceField,
  EncryptedField,
  FileUploadField,
  InputAlertField,
  InputField,
  ObjectField,
  TextAreaField,
} from './SharedFields';
import en from '../../../locales/en/messages';

describe('Setting form fields', () => {
  test('BooleanField renders the expected content', async () => {
    i18n.loadLocaleData({ en: { plurals: en } });
    i18n.load({ en });
    i18n.activate('en');
    const wrapper = mountWithContexts(
      <I18nProvider i18n={i18n}>
        <Formik
          initialValues={{
            boolean: true,
          }}
        >
          {() => (
            <BooleanField
              name="boolean"
              config={{
                label: 'test',
                help_text: 'test',
              }}
            />
          )}
        </Formik>
      </I18nProvider>
    );
    expect(wrapper.find('Switch')).toHaveLength(1);
    expect(wrapper.find('Switch').prop('isChecked')).toBe(true);
    expect(wrapper.find('Switch').prop('isDisabled')).toBe(false);
    await act(async () => {
      wrapper.find('Switch').invoke('onChange')();
    });
    wrapper.update();
    expect(wrapper.find('Switch').prop('isChecked')).toBe(false);
  });

  test('ChoiceField renders unrequired form field', async () => {
    const wrapper = mountWithContexts(
      <Formik
        initialValues={{
          choice: 'one',
        }}
      >
        {() => (
          <ChoiceField
            name="choice"
            config={{
              label: 'test',
              help_text: 'test',
              choices: [
                ['one', 'One'],
                ['two', 'Two'],
              ],
            }}
          />
        )}
      </Formik>
    );
    expect(wrapper.find('FormSelect')).toHaveLength(1);
    expect(wrapper.find('.pf-c-form__label-required')).toHaveLength(0);
  });

  test('EncryptedField renders the expected content', async () => {
    const wrapper = mountWithContexts(
      <Formik
        initialValues={{
          encrypted: '',
        }}
      >
        {() => (
          <EncryptedField
            name="encrypted"
            config={{
              label: 'test',
              help_text: 'test',
            }}
          />
        )}
      </Formik>
    );
    expect(wrapper.find('PasswordInput')).toHaveLength(1);
  });

  test('InputField renders the expected content', async () => {
    const wrapper = mountWithContexts(
      <Formik
        initialValues={{
          text: '',
        }}
      >
        {() => (
          <InputField
            name="text"
            config={{
              label: 'test',
              help_text: 'test',
              default: '',
            }}
          />
        )}
      </Formik>
    );
    expect(wrapper.find('TextInputBase')).toHaveLength(1);
    expect(wrapper.find('TextInputBase').prop('value')).toEqual('');
    await act(async () => {
      wrapper.find('TextInputBase').invoke('onChange')(null, {
        target: {
          name: 'text',
          value: 'foo',
        },
      });
    });
    wrapper.update();
    expect(wrapper.find('TextInputBase').prop('value')).toEqual('foo');
  });

  test('InputField should revert to expected default value', async () => {
    const wrapper = mountWithContexts(
      <Formik
        initialValues={{
          number: 5,
        }}
      >
        {() => (
          <InputField
            name="number"
            type="number"
            config={{
              label: 'test number input',
              min_value: -10,
              default: 0,
            }}
          />
        )}
      </Formik>
    );
    expect(wrapper.find('TextInputBase')).toHaveLength(1);
    expect(wrapper.find('TextInputBase').prop('value')).toEqual(5);
    await act(async () => {
      wrapper.find('button[aria-label="Revert"]').invoke('onClick')();
    });
    wrapper.update();
    expect(wrapper.find('TextInputBase').prop('value')).toEqual(0);
  });

  test('InputAlertField initially renders disable TextInput', async () => {
    const wrapper = mountWithContexts(
      <Formik
        initialValues={{
          text: '',
        }}
      >
        {() => (
          <InputAlertField
            name="text"
            config={{
              label: 'test',
              help_text: 'test',
              default: '',
            }}
          />
        )}
      </Formik>
    );
    expect(wrapper.find('TextInput')).toHaveLength(1);
    expect(wrapper.find('TextInput').prop('value')).toEqual('');
    expect(wrapper.find('TextInput').prop('isDisabled')).toBe(true);
  });

  test('TextAreaField renders the expected content', async () => {
    const wrapper = mountWithContexts(
      <Formik
        initialValues={{
          mock_textarea: '',
        }}
      >
        {() => (
          <TextAreaField
            name="mock_textarea"
            config={{
              label: 'mock textarea',
              help_text: 'help text',
              default: '',
            }}
          />
        )}
      </Formik>
    );
    expect(wrapper.find('textarea')).toHaveLength(1);
    expect(wrapper.find('textarea#mock_textarea').prop('value')).toEqual('');
    await act(async () => {
      wrapper.find('textarea#mock_textarea').simulate('change', {
        target: { value: 'new textarea value', name: 'mock_textarea' },
      });
    });
    wrapper.update();
    expect(wrapper.find('textarea').prop('value')).toEqual(
      'new textarea value'
    );
  });

  test('ObjectField renders the expected content', async () => {
    const wrapper = mountWithContexts(
      <Formik
        initialValues={{
          object: '["one", "two", "three"]',
        }}
      >
        {() => (
          <ObjectField
            name="object"
            config={{
              label: 'test',
              help_text: 'test',
              default: '[]',
              type: 'list',
            }}
          />
        )}
      </Formik>
    );
    expect(wrapper.find('CodeEditor')).toHaveLength(1);
    expect(wrapper.find('CodeEditor').prop('value')).toBe(
      '["one", "two", "three"]'
    );
    await act(async () => {
      wrapper.find('CodeEditor').invoke('onChange')('[]');
    });
    wrapper.update();
    expect(wrapper.find('CodeEditor').prop('value')).toBe('[]');
  });

  test('FileUploadField renders the expected content', async () => {
    const wrapper = mountWithContexts(
      <Formik
        initialValues={{
          mock_file: 'mock file value',
        }}
      >
        {() => (
          <FileUploadField
            name="mock_file"
            config={{
              label: 'mock file label',
              help_text: 'mock file help',
              default: '',
            }}
          />
        )}
      </Formik>
    );

    expect(
      wrapper.find('FileUploadField[value="mock file value"]')
    ).toHaveLength(1);
    expect(wrapper.find('label').text()).toEqual('mock file label');
    expect(wrapper.find('input#mock_file-filename').prop('value')).toEqual('');
    await act(async () => {
      wrapper.find('FileUpload').invoke('onChange')(
        {
          text: () =>
            '-----BEGIN PRIVATE KEY-----\\nAAAAAAAAAAAAAA\\n-----END PRIVATE KEY-----\\n',
        },
        'new file name'
      );
    });
    wrapper.update();
    expect(wrapper.find('input#mock_file-filename').prop('value')).toEqual(
      'new file name'
    );
    await act(async () => {
      wrapper.find('button[aria-label="Revert"]').invoke('onClick')();
    });
    wrapper.update();
    expect(wrapper.find('input#mock_file-filename').prop('value')).toEqual('');
  });
  test('should render confirmation modal when toggle on for disable local auth', async () => {
    const wrapper = mountWithContexts(
      <Formik
        initialValues={{
          DISABLE_LOCAL_AUTH: false,
        }}
      >
        {() => (
          <BooleanField
            name="DISABLE_LOCAL_AUTH"
            needsConfirmationModal
            modalTitle="Confirm Disable Local Authorization"
            config={{
              category: 'Authentication',
              category_slug: 'authentication',
              default: false,
              help_text:
                'Controls whether users are prevented from using the built-in authentication system. You probably want to do this if you are using an LDAP or SAML integration.',
              label: 'Disable the built-in authentication system',
              required: true,
              type: 'boolean',
              value: false,
            }}
          />
        )}
      </Formik>
    );
    expect(wrapper.find('Switch')).toHaveLength(1);
    expect(wrapper.find('Switch').prop('isChecked')).toBe(false);
    expect(wrapper.find('Switch').prop('isDisabled')).toBe(false);
    await act(async () => {
      wrapper.find('Switch').invoke('onChange')(true);
    });
    wrapper.update();

    expect(wrapper.find('AlertModal')).toHaveLength(1);
    expect(
      wrapper.find('BooleanField[name="DISABLE_LOCAL_AUTH"]')
    ).toHaveLength(1);
    await act(async () =>
      wrapper
        .find('Button[ouiaId="confirm-misc-settings-modal"]')
        .prop('onClick')()
    );
    wrapper.update();
    expect(wrapper.find('AlertModal')).toHaveLength(0);
    expect(wrapper.find('Switch').prop('isChecked')).toBe(true);
  });

  test('should not render confirmation modal when toggling off', async () => {
    const wrapper = mountWithContexts(
      <Formik
        initialValues={{
          DISABLE_LOCAL_AUTH: true,
        }}
      >
        {() => (
          <BooleanField
            name="DISABLE_LOCAL_AUTH"
            needsConfirmationModal
            modalTitle="Confirm Disable Local Authorization"
            config={{
              category: 'Authentication',
              category_slug: 'authentication',
              default: false,
              help_text:
                'Controls whether users are prevented from using the built-in authentication system. You probably want to do this if you are using an LDAP or SAML integration.',
              label: 'Disable the built-in authentication system',
              required: true,
              type: 'boolean',
              value: false,
            }}
          />
        )}
      </Formik>
    );
    expect(wrapper.find('Switch')).toHaveLength(1);
    expect(wrapper.find('Switch').prop('isChecked')).toBe(true);
    expect(wrapper.find('Switch').prop('isDisabled')).toBe(false);
    await act(async () => {
      wrapper.find('Switch').invoke('onChange')(false);
    });
    wrapper.update();
    expect(wrapper.find('AlertModal')).toHaveLength(0);
    expect(wrapper.find('Switch').prop('isChecked')).toBe(false);
  });

  test('should not toggle disable local auth', async () => {
    const wrapper = mountWithContexts(
      <Formik
        initialValues={{
          DISABLE_LOCAL_AUTH: false,
        }}
      >
        {() => (
          <BooleanField
            name="DISABLE_LOCAL_AUTH"
            needsConfirmationModal
            modalTitle="Confirm Disable Local Authorization"
            config={{
              category: 'Authentication',
              category_slug: 'authentication',
              default: false,
              help_text:
                'Controls whether users are prevented from using the built-in authentication system. You probably want to do this if you are using an LDAP or SAML integration.',
              label: 'Disable the built-in authentication system',
              required: true,
              type: 'boolean',
              value: false,
            }}
          />
        )}
      </Formik>
    );
    expect(wrapper.find('Switch')).toHaveLength(1);
    expect(wrapper.find('Switch').prop('isChecked')).toBe(false);
    expect(wrapper.find('Switch').prop('isDisabled')).toBe(false);
    await act(async () => {
      wrapper.find('Switch').invoke('onChange')(true);
    });
    wrapper.update();

    expect(wrapper.find('AlertModal')).toHaveLength(1);
    await act(async () =>
      wrapper
        .find('Button[ouiaId="cancel-misc-settings-modal"]')
        .prop('onClick')()
    );
    wrapper.update();

    expect(wrapper.find('AlertModal')).toHaveLength(0);
    expect(wrapper.find('Switch').prop('isChecked')).toBe(false);
  });
});
