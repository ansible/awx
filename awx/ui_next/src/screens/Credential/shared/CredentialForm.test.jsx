import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import CredentialForm from './CredentialForm';

jest.mock('@api');

const machineCredential = {
  id: 3,
  type: 'credential',
  url: '/api/v2/credentials/3/',
  related: {
    named_url: '/api/v2/credentials/oersdgfasf++Machine+ssh++org/',
    created_by: '/api/v2/users/1/',
    modified_by: '/api/v2/users/1/',
    organization: '/api/v2/organizations/1/',
    activity_stream: '/api/v2/credentials/3/activity_stream/',
    access_list: '/api/v2/credentials/3/access_list/',
    object_roles: '/api/v2/credentials/3/object_roles/',
    owner_users: '/api/v2/credentials/3/owner_users/',
    owner_teams: '/api/v2/credentials/3/owner_teams/',
    copy: '/api/v2/credentials/3/copy/',
    input_sources: '/api/v2/credentials/3/input_sources/',
    credential_type: '/api/v2/credential_types/1/',
  },
  summary_fields: {
    organization: {
      id: 1,
      name: 'org',
      description: '',
    },
    credential_type: {
      id: 1,
      name: 'Machine',
      description: '',
    },
    created_by: {
      id: 1,
      username: 'admin',
      first_name: '',
      last_name: '',
    },
    modified_by: {
      id: 1,
      username: 'admin',
      first_name: '',
      last_name: '',
    },
    object_roles: {
      admin_role: {
        description: 'Can manage all aspects of the credential',
        name: 'Admin',
        id: 36,
      },
      use_role: {
        description: 'Can use the credential in a job template',
        name: 'Use',
        id: 37,
      },
      read_role: {
        description: 'May view settings for the credential',
        name: 'Read',
        id: 38,
      },
    },
    user_capabilities: {
      edit: true,
      delete: true,
      copy: true,
      use: true,
    },
    owners: [
      {
        id: 1,
        type: 'user',
        name: 'admin',
        description: ' ',
        url: '/api/v2/users/1/',
      },
      {
        id: 1,
        type: 'organization',
        name: 'org',
        description: '',
        url: '/api/v2/organizations/1/',
      },
    ],
  },
  created: '2020-02-18T15:35:04.563928Z',
  modified: '2020-02-18T15:35:04.563957Z',
  name: 'oersdgfasf',
  description: '',
  organization: 1,
  credential_type: 1,
  inputs: {},
  kind: 'ssh',
  cloud: false,
  kubernetes: false,
};

const sourceControlCredential = {
  id: 4,
  type: 'credential',
  url: '/api/v2/credentials/4/',
  related: {
    named_url: '/api/v2/credentials/joijoij++Source Control+scm++/',
    created_by: '/api/v2/users/1/',
    modified_by: '/api/v2/users/1/',
    activity_stream: '/api/v2/credentials/4/activity_stream/',
    access_list: '/api/v2/credentials/4/access_list/',
    object_roles: '/api/v2/credentials/4/object_roles/',
    owner_users: '/api/v2/credentials/4/owner_users/',
    owner_teams: '/api/v2/credentials/4/owner_teams/',
    copy: '/api/v2/credentials/4/copy/',
    input_sources: '/api/v2/credentials/4/input_sources/',
    credential_type: '/api/v2/credential_types/2/',
    user: '/api/v2/users/1/',
  },
  summary_fields: {
    credential_type: {
      id: 2,
      name: 'Source Control',
      description: '',
    },
    created_by: {
      id: 1,
      username: 'admin',
      first_name: '',
      last_name: '',
    },
    modified_by: {
      id: 1,
      username: 'admin',
      first_name: '',
      last_name: '',
    },
    object_roles: {
      admin_role: {
        description: 'Can manage all aspects of the credential',
        name: 'Admin',
        id: 39,
      },
      use_role: {
        description: 'Can use the credential in a job template',
        name: 'Use',
        id: 40,
      },
      read_role: {
        description: 'May view settings for the credential',
        name: 'Read',
        id: 41,
      },
    },
    user_capabilities: {
      edit: true,
      delete: true,
      copy: true,
      use: true,
    },
    owners: [
      {
        id: 1,
        type: 'user',
        name: 'admin',
        description: ' ',
        url: '/api/v2/users/1/',
      },
    ],
  },
  created: '2020-02-18T16:03:01.366287Z',
  modified: '2020-02-18T16:03:01.366315Z',
  name: 'joijoij',
  description: 'ojiojojo',
  organization: null,
  credential_type: 2,
  inputs: {
    ssh_key_unlock: '$encrypted$',
  },
  kind: 'scm',
  cloud: false,
  kubernetes: false,
};

const gceCredential = {
  id: 9,
  type: 'credential',
  url: '/api/v2/credentials/9/',
  related: {
    named_url:
      '/api/v2/credentials/a gce cred++Google Compute Engine+cloud++Default/',
    created_by: '/api/v2/users/1/',
    modified_by: '/api/v2/users/1/',
    organization: '/api/v2/organizations/4/',
    activity_stream: '/api/v2/credentials/9/activity_stream/',
    access_list: '/api/v2/credentials/9/access_list/',
    object_roles: '/api/v2/credentials/9/object_roles/',
    owner_users: '/api/v2/credentials/9/owner_users/',
    owner_teams: '/api/v2/credentials/9/owner_teams/',
    copy: '/api/v2/credentials/9/copy/',
    input_sources: '/api/v2/credentials/9/input_sources/',
    credential_type: '/api/v2/credential_types/10/',
  },
  summary_fields: {
    organization: {
      id: 4,
      name: 'Default',
      description: '',
    },
    credential_type: {
      id: 10,
      name: 'Google Compute Engine',
      description: '',
    },
    created_by: {
      id: 1,
      username: 'admin',
      first_name: '',
      last_name: '',
    },
    modified_by: {
      id: 1,
      username: 'admin',
      first_name: '',
      last_name: '',
    },
    object_roles: {
      admin_role: {
        description: 'Can manage all aspects of the credential',
        name: 'Admin',
        id: 287,
      },
      use_role: {
        description: 'Can use the credential in a job template',
        name: 'Use',
        id: 288,
      },
      read_role: {
        description: 'May view settings for the credential',
        name: 'Read',
        id: 289,
      },
    },
    user_capabilities: {
      edit: true,
      delete: true,
      copy: true,
      use: true,
    },
    owners: [
      {
        id: 1,
        type: 'user',
        name: 'admin',
        description: ' ',
        url: '/api/v2/users/1/',
      },
      {
        id: 4,
        type: 'organization',
        name: 'Default',
        description: '',
        url: '/api/v2/organizations/4/',
      },
    ],
  },
  created: '2020-04-13T17:33:27.625773Z',
  modified: '2020-04-13T17:33:27.625882Z',
  name: 'a gce cred',
  description: '',
  organization: 4,
  credential_type: 10,
  inputs: {
    project: 'test123',
    username: 'test123.iam.gserviceaccount.com',
    ssh_key_data: '$encrypted$',
  },
  kind: 'gce',
  cloud: true,
  kubernetes: false,
};

const credentialTypes = [
  {
    id: 2,
    type: 'credential_type',
    url: '/api/v2/credential_types/2/',
    related: {
      credentials: '/api/v2/credential_types/2/credentials/',
      activity_stream: '/api/v2/credential_types/2/activity_stream/',
    },
    summary_fields: {
      user_capabilities: {
        edit: false,
        delete: false,
      },
    },
    created: '2020-02-12T19:42:43.551238Z',
    modified: '2020-02-12T19:43:03.164800Z',
    name: 'Source Control',
    description: '',
    kind: 'scm',
    namespace: 'scm',
    managed_by_tower: true,
    inputs: {
      fields: [
        {
          id: 'username',
          label: 'Username',
          type: 'string',
        },
        {
          id: 'password',
          label: 'Password',
          type: 'string',
          secret: true,
        },
        {
          id: 'ssh_key_data',
          label: 'Source Control Private Key',
          type: 'string',
          format: 'ssh_private_key',
          secret: true,
          multiline: true,
        },
        {
          id: 'ssh_key_unlock',
          label: 'Private Key Passphrase',
          type: 'string',
          secret: true,
        },
      ],
    },
    injectors: {},
  },
  {
    id: 1,
    type: 'credential_type',
    url: '/api/v2/credential_types/1/',
    related: {
      credentials: '/api/v2/credential_types/1/credentials/',
      activity_stream: '/api/v2/credential_types/1/activity_stream/',
    },
    summary_fields: {
      user_capabilities: {
        edit: false,
        delete: false,
      },
    },
    created: '2020-02-12T19:42:43.539626Z',
    modified: '2020-02-12T19:43:03.159739Z',
    name: 'Machine',
    description: '',
    kind: 'ssh',
    namespace: 'ssh',
    managed_by_tower: true,
    inputs: {
      fields: [
        {
          id: 'username',
          label: 'Username',
          type: 'string',
        },
        {
          id: 'password',
          label: 'Password',
          type: 'string',
          secret: true,
          ask_at_runtime: true,
        },
        {
          id: 'ssh_key_data',
          label: 'SSH Private Key',
          type: 'string',
          format: 'ssh_private_key',
          secret: true,
          multiline: true,
        },
        {
          id: 'ssh_public_key_data',
          label: 'Signed SSH Certificate',
          type: 'string',
          multiline: true,
          secret: true,
        },
        {
          id: 'ssh_key_unlock',
          label: 'Private Key Passphrase',
          type: 'string',
          secret: true,
          ask_at_runtime: true,
        },
        {
          id: 'become_method',
          label: 'Privilege Escalation Method',
          type: 'string',
          help_text:
            'Specify a method for "become" operations. This is equivalent to specifying the --become-method Ansible parameter.',
        },
        {
          id: 'become_username',
          label: 'Privilege Escalation Username',
          type: 'string',
        },
        {
          id: 'become_password',
          label: 'Privilege Escalation Password',
          type: 'string',
          secret: true,
          ask_at_runtime: true,
        },
      ],
    },
    injectors: {},
  },
  {
    id: 10,
    type: 'credential_type',
    url: '/api/v2/credential_types/10/',
    related: {
      credentials: '/api/v2/credential_types/10/credentials/',
      activity_stream: '/api/v2/credential_types/10/activity_stream/',
    },
    summary_fields: {
      user_capabilities: {
        edit: false,
        delete: false,
      },
    },
    created: '2020-04-09T19:20:27.090665Z',
    modified: '2020-04-09T19:21:11.575214Z',
    name: 'Google Compute Engine',
    description: '',
    kind: 'cloud',
    namespace: 'gce',
    managed_by_tower: true,
    inputs: {
      fields: [
        {
          id: 'username',
          label: 'Service Account Email Address',
          type: 'string',
          help_text:
            'The email address assigned to the Google Compute Engine service account.',
        },
        {
          id: 'project',
          label: 'Project',
          type: 'string',
          help_text:
            'The Project ID is the GCE assigned identification. It is often constructed as three words or two words followed by a three-digit number. Examples: project-id-000 and another-project-id',
        },
        {
          id: 'ssh_key_data',
          label: 'RSA Private Key',
          type: 'string',
          format: 'ssh_private_key',
          secret: true,
          multiline: true,
          help_text:
            'Paste the contents of the PEM file associated with the service account email.',
        },
      ],
      required: ['username', 'ssh_key_data'],
    },
    injectors: {},
  },
];

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
    expect(wrapper.find('FormGroup[label="Password"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="SSH Private Key"]').length).toBe(1);
    expect(
      wrapper.find('FormGroup[label="Signed SSH Certificate"]').length
    ).toBe(1);
    expect(
      wrapper.find('FormGroup[label="Private Key Passphrase"]').length
    ).toBe(1);
    expect(
      wrapper.find('FormGroup[label="Privelege Escalation Method"]').length
    ).toBe(1);
    expect(
      wrapper.find('FormGroup[label="Privilege Escalation Username"]').length
    ).toBe(1);
    expect(
      wrapper.find('FormGroup[label="Privilege Escalation Password"]').length
    ).toBe(1);
  };

  const sourceFieldExpects = () => {
    expect(wrapper.find('FormGroup').length).toBe(8);
    expect(wrapper.find('FormGroup[label="Name"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Description"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Organization"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Credential Type"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Username"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Password"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="SSH Private Key"]').length).toBe(1);
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
      wrapper.find('FormGroup[label="Service account email address"]').length
    ).toBe(1);
    expect(wrapper.find('FormGroup[label="Project"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="RSA private key"]').length).toBe(1);
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
          .find('AnsibleSelect[id="credential_type"]')
          .invoke('onChange')(null, 1);
      });
      wrapper.update();
      machineFieldExpects();
      await act(async () => {
        await wrapper
          .find('AnsibleSelect[id="credential_type"]')
          .invoke('onChange')(null, 2);
      });
      wrapper.update();
      sourceFieldExpects();
    });
    test('should update expected fields when gce service account json file uploaded', async () => {
      await act(async () => {
        await wrapper
          .find('AnsibleSelect[id="credential_type"]')
          .invoke('onChange')(null, 10);
      });
      wrapper.update();
      gceFieldExpects();
      expect(wrapper.find('input#credential-username').prop('value')).toBe('');
      expect(wrapper.find('input#credential-project').prop('value')).toBe('');
      expect(wrapper.find('textarea#credential-sshKeyData').prop('value')).toBe(
        ''
      );
      await act(async () => {
        wrapper.find('FileUpload').invoke('onChange')({
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
      expect(wrapper.find('textarea#credential-sshKeyData').prop('value')).toBe(
        '-----BEGIN PRIVATE KEY-----\nAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n-----END PRIVATE KEY-----\n'
      );
    });
    test('should clear expected fields when file clear button clicked', async () => {
      await act(async () => {
        wrapper.find('FileUploadField').invoke('onClearButtonClick')();
      });
      wrapper.update();
      expect(wrapper.find('input#credential-username').prop('value')).toBe('');
      expect(wrapper.find('input#credential-project').prop('value')).toBe('');
      expect(wrapper.find('textarea#credential-sshKeyData').prop('value')).toBe(
        ''
      );
    });
    test('should show error when error thrown parsing JSON', async () => {
      expect(wrapper.find('#credential-gce-file-helper').text()).toBe(
        'Select a JSON formatted service account key to autopopulate the following fields.'
      );
      await act(async () => {
        wrapper.find('FileUpload').invoke('onChange')({
          name: 'foo.json',
          text: () => '{not good json}',
        });
      });
      wrapper.update();
      expect(wrapper.find('#credential-gce-file-helper').text()).toBe(
        'There was an error parsing the file. Please check the file formatting and try again.'
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
            credential={sourceControlCredential}
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
