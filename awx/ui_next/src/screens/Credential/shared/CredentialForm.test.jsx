import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import machineCredential from './data.machineCredential.json';
import gceCredential from './data.gceCredential.json';
import scmCredential from './data.scmCredential.json';
import credentialTypesArr from './data.credentialTypes.json';
import CredentialForm from './CredentialForm';

jest.mock('../../../api');

const credentialTypes = credentialTypesArr.reduce(
  (credentialTypesMap, credentialType) => {
    credentialTypesMap[credentialType.id] = credentialType;
    return credentialTypesMap;
  },
  {}
);

describe('<CredentialForm />', () => {
  let wrapper;
  const onCancel = jest.fn();
  const onSubmit = jest.fn();

  const addFieldExpects = () => {
    expect(wrapper.find('FormGroup').length).toBe(4);
    expect(wrapper.find('FormGroup[label="Name"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Description"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Organization"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Credential Type"]').length).toBe(1);
  };

  const machineFieldExpects = () => {
    expect(wrapper.find('FormGroup[label="Name"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Description"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Organization"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Credential Type"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Username"]').length).toBe(1);
    expect(wrapper.find('input#credential-password').length).toBe(1);
    expect(wrapper.find('FormGroup[label="SSH Private Key"]').length).toBe(1);
    expect(
      wrapper.find('FormGroup[label="Signed SSH Certificate"]').length
    ).toBe(1);
    expect(wrapper.find('input#credential-ssh_key_unlock').length).toBe(1);
    expect(
      wrapper.find('FormGroup[label="Privilege Escalation Method"]').length
    ).toBe(1);
    expect(
      wrapper.find('FormGroup[label="Privilege Escalation Username"]').length
    ).toBe(1);
    expect(wrapper.find('input#credential-become_password').length).toBe(1);
  };

  const sourceFieldExpects = () => {
    expect(wrapper.find('FormGroup').length).toBe(8);
    expect(wrapper.find('FormGroup[label="Name"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Description"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Organization"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Credential Type"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Username"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Password"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="SCM Private Key"]').length).toBe(1);
    expect(
      wrapper.find('FormGroup[label="Private Key Passphrase"]').length
    ).toBe(1);
  };

  const gceFieldExpects = () => {
    expect(wrapper.find('FormGroup').length).toBe(8);
    expect(wrapper.find('FormGroup[label="Name"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Description"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Organization"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Credential Type"]').length).toBe(1);
    expect(
      wrapper.find('FormGroup[label="Service account JSON file"]').length
    ).toBe(1);
    expect(
      wrapper.find('FormGroup[label="Service Account Email Address"]').length
    ).toBe(1);
    expect(wrapper.find('FormGroup[label="Project"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="RSA Private Key"]').length).toBe(1);
  };

  describe('Add', () => {
    beforeAll(async () => {
      await act(async () => {
        wrapper = mountWithContexts(
          <CredentialForm
            onCancel={onCancel}
            onSubmit={onSubmit}
            credentialTypes={credentialTypes}
          />
        );
      });
    });
    afterAll(() => {
      wrapper.unmount();
    });
    test('should display form fields on add properly', async () => {
      addFieldExpects();
    });
    test('should hide Test button initially', () => {
      expect(wrapper.find('Button[children="Test"]').length).toBe(0);
    });
    test('should update form values', async () => {
      // name and description change
      await act(async () => {
        wrapper.find('input#credential-name').simulate('change', {
          target: { value: 'new Foo', name: 'name' },
        });
        wrapper.find('input#credential-description').simulate('change', {
          target: { value: 'new Bar', name: 'description' },
        });
      });
      wrapper.update();
      expect(wrapper.find('input#credential-name').prop('value')).toEqual(
        'new Foo'
      );
      expect(
        wrapper.find('input#credential-description').prop('value')
      ).toEqual('new Bar');
      // organization change
      await act(async () => {
        wrapper.find('OrganizationLookup').invoke('onBlur')();
        wrapper.find('OrganizationLookup').invoke('onChange')({
          id: 3,
          name: 'organization',
        });
      });
      wrapper.update();
      expect(wrapper.find('OrganizationLookup').prop('value')).toEqual({
        id: 3,
        name: 'organization',
      });
    });
    test('should display cred type subform when scm type select has a value', async () => {
      await act(async () => {
        await wrapper
          .find('AnsibleSelect[id="credential-type"]')
          .invoke('onChange')(null, 1);
      });
      wrapper.update();
      machineFieldExpects();
      await act(async () => {
        await wrapper
          .find('AnsibleSelect[id="credential-type"]')
          .invoke('onChange')(null, 2);
      });
      wrapper.update();
      sourceFieldExpects();
    });

    test('should update expected fields when gce service account json file uploaded', async () => {
      await act(async () => {
        await wrapper
          .find('AnsibleSelect[id="credential-type"]')
          .invoke('onChange')(null, 10);
      });
      wrapper.update();
      gceFieldExpects();
      expect(wrapper.find('input#credential-username').prop('value')).toBe('');
      expect(wrapper.find('input#credential-project').prop('value')).toBe('');
      expect(
        wrapper.find('textarea#credential-ssh_key_data').prop('value')
      ).toBe('');
      await act(async () => {
        wrapper.find('FileUpload#credential-gce-file').invoke('onChange')({
          name: 'foo.json',
          text: () =>
            '{"client_email":"testemail@ansible.com","project_id":"test123","private_key":"-----BEGIN PRIVATE KEY-----\\nAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\\n-----END PRIVATE KEY-----\\n"}',
        });
      });
      wrapper.update();
      expect(wrapper.find('input#credential-username').prop('value')).toBe(
        'testemail@ansible.com'
      );
      expect(wrapper.find('input#credential-project').prop('value')).toBe(
        'test123'
      );
      expect(
        wrapper.find('textarea#credential-ssh_key_data').prop('value')
      ).toBe(
        '-----BEGIN PRIVATE KEY-----\nAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n-----END PRIVATE KEY-----\n'
      );
    });

    test('should clear expected fields when file clear button clicked', async () => {
      await act(async () => {
        wrapper
          .find('FileUploadField#credential-gce-file')
          .invoke('onClearButtonClick')();
      });
      wrapper.update();
      expect(wrapper.find('input#credential-username').prop('value')).toBe('');
      expect(wrapper.find('input#credential-project').prop('value')).toBe('');
      expect(
        wrapper.find('textarea#credential-ssh_key_data').prop('value')
      ).toBe('');
    });
    test('should update field when RSA Private Key file uploaded', async () => {
      await act(async () => {
        wrapper.find('FileUpload#credential-ssh_key_data').invoke('onChange')(
          '-----BEGIN PRIVATE KEY-----\\nBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB\\n-----END PRIVATE KEY-----\\n',
          'foo.key'
        );
      });
      wrapper.update();
      expect(
        wrapper.find('textarea#credential-ssh_key_data').prop('value')
      ).toBe(
        '-----BEGIN PRIVATE KEY-----\\nBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB\\n-----END PRIVATE KEY-----\\n'
      );
    });
    test('should show error when error thrown parsing JSON', async () => {
      await act(async () => {
        await wrapper
          .find('AnsibleSelect[id="credential-type"]')
          .invoke('onChange')(null, 10);
      });
      wrapper.update();
      expect(wrapper.find('#credential-gce-file-helper').text()).toBe(
        'Select a JSON formatted service account key to autopopulate the following fields.'
      );
      await act(async () => {
        wrapper.find('FileUpload#credential-gce-file').invoke('onChange')({
          name: 'foo.json',
          text: () => '{not good json}',
        });
      });
      wrapper.update();
      expect(
        wrapper
          .find('FormGroup[fieldId="credential-gce-file"]')
          .prop('validated')
      ).toBe('error');

      expect(
        wrapper
          .find('FormGroup[fieldId="credential-gce-file"]')
          .prop('helperTextInvalid')
      ).toBe(
        'There was an error parsing the file. Please check the file formatting and try again.'
      );
    });
    test('should show Test button when external credential type is selected', async () => {
      await act(async () => {
        await wrapper
          .find('AnsibleSelect[id="credential-type"]')
          .invoke('onChange')(null, 21);
      });
      wrapper.update();
      expect(wrapper.find('Button[children="Test"]').length).toBe(1);
      expect(wrapper.find('Button[children="Test"]').props().isDisabled).toBe(
        true
      );
    });
    test('should call handleCancel when Cancel button is clicked', async () => {
      expect(onCancel).not.toHaveBeenCalled();
      wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
      expect(onCancel).toBeCalled();
    });
  });

  describe('Edit', () => {
    afterEach(() => {
      wrapper.unmount();
    });
    test('Initially renders successfully', async () => {
      await act(async () => {
        wrapper = mountWithContexts(
          <CredentialForm
            onCancel={onCancel}
            onSubmit={onSubmit}
            credential={machineCredential}
            credentialTypes={credentialTypes}
          />
        );
      });

      expect(wrapper.length).toBe(1);
    });

    test('should display form fields for machine credential properly', async () => {
      await act(async () => {
        wrapper = mountWithContexts(
          <CredentialForm
            onCancel={onCancel}
            onSubmit={onSubmit}
            credential={machineCredential}
            credentialTypes={credentialTypes}
          />
        );
      });

      machineFieldExpects();
    });

    test('should display form fields for source control credential properly', async () => {
      await act(async () => {
        wrapper = mountWithContexts(
          <CredentialForm
            onCancel={onCancel}
            onSubmit={onSubmit}
            credential={scmCredential}
            credentialTypes={credentialTypes}
          />
        );
      });

      sourceFieldExpects();
    });

    test('should display form fields for gce credential properly', async () => {
      await act(async () => {
        wrapper = mountWithContexts(
          <CredentialForm
            onCancel={onCancel}
            onSubmit={onSubmit}
            credential={gceCredential}
            credentialTypes={credentialTypes}
          />
        );
      });

      gceFieldExpects();
    });
  });
});
