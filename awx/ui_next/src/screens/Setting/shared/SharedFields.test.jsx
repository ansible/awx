import React from 'react';
import { mount } from 'enzyme';
import { Formik } from 'formik';
import { I18nProvider } from '@lingui/react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import {
  BooleanField,
  ChoiceField,
  EncryptedField,
  FileUploadField,
  InputField,
  ObjectField,
  TextAreaField,
} from './SharedFields';

describe('Setting form fields', () => {
  test('BooleanField renders the expected content', async () => {
    const outerNode = document.createElement('div');
    document.body.appendChild(outerNode);
    const wrapper = mount(
      <I18nProvider>
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
      </I18nProvider>,
      {
        attachTo: outerNode,
      }
    );
    expect(wrapper.find('Switch')).toHaveLength(1);
    expect(wrapper.find('Switch').prop('isChecked')).toBe(true);
    expect(wrapper.find('Switch').prop('isDisabled')).toBe(false);
    await act(async () => {
      wrapper
        .find('Switch label')
        .instance()
        .dispatchEvent(new Event('click'));
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
    expect(wrapper.find('CodeMirrorInput')).toHaveLength(1);
    expect(wrapper.find('CodeMirrorInput').prop('value')).toBe(
      '["one", "two", "three"]'
    );
    await act(async () => {
      wrapper.find('CodeMirrorInput').invoke('onChange')('[]');
    });
    wrapper.update();
    expect(wrapper.find('CodeMirrorInput').prop('value')).toBe('[]');
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
    expect(wrapper.find('FileUploadField')).toHaveLength(1);
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
});
