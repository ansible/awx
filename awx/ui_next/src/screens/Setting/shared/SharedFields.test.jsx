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
  InputField,
  ObjectField,
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
});
