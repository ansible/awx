import React from 'react';
import { Formik } from 'formik';
import { TextInput } from '@patternfly/react-core';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import CredentialPluginField from './CredentialPluginField';

const fieldOptions = {
  id: 'username',
  label: 'Username',
  type: 'string',
};

describe('<CredentialPluginField />', () => {
  let wrapper;
  describe('No plugin configured', () => {
    beforeAll(() => {
      wrapper = mountWithContexts(
        <Formik
          initialValues={{
            inputs: {
              username: '',
            },
          }}
        >
          {() => (
            <CredentialPluginField
              fieldOptions={fieldOptions}
              isDisabled={false}
              isRequired={false}
            >
              <TextInput id="credential-username" />
            </CredentialPluginField>
          )}
        </Formik>
      );
    });
    afterAll(() => {
      wrapper.unmount();
    });
    test('renders the expected content', () => {
      expect(wrapper.find('input').length).toBe(1);
      expect(wrapper.find('KeyIcon').length).toBe(1);
      expect(wrapper.find('CredentialPluginSelected').length).toBe(0);
    });
    test('clicking plugin button shows plugin prompt', () => {
      expect(wrapper.find('CredentialPluginPrompt').length).toBe(0);
      wrapper.find('KeyIcon').simulate('click');
      expect(wrapper.find('CredentialPluginPrompt').length).toBe(1);
    });
  });
  describe('Plugin already configured', () => {
    beforeAll(() => {
      wrapper = mountWithContexts(
        <Formik
          initialValues={{
            inputs: {
              username: {
                credential: {
                  id: 1,
                  name: 'CyberArk Cred',
                  cloud: false,
                  credential_type_id: 20,
                  kind: 'conjur',
                },
              },
            },
          }}
        >
          {() => (
            <CredentialPluginField
              fieldOptions={fieldOptions}
              isDisabled={false}
              isRequired={false}
            >
              <TextInput id="credential-username" />
            </CredentialPluginField>
          )}
        </Formik>
      );
    });
    afterAll(() => {
      wrapper.unmount();
    });
    test('renders the expected content', () => {
      expect(wrapper.find('CredentialPluginPrompt').length).toBe(0);
      expect(wrapper.find('input').length).toBe(0);
      expect(wrapper.find('KeyIcon').length).toBe(1);
      expect(wrapper.find('CredentialPluginSelected').length).toBe(1);
    });
  });
});
