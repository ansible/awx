import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  CredentialsAPI,
  CredentialTypesAPI,
  JobTemplatesAPI,
  LabelsAPI,
  ProjectsAPI,
  InventoriesAPI,
  ExecutionEnvironmentsAPI,
  InstanceGroupsAPI,
  RootAPI,
} from 'api';
import useDebounce from 'hooks/useDebounce';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import JobTemplateEdit from './JobTemplateEdit';

jest.mock('../../../hooks/useDebounce');
jest.mock('../../../api/models/Credentials');
jest.mock('../../../api/models/CredentialTypes');
jest.mock('../../../api/models/JobTemplates');
jest.mock('../../../api/models/Labels');
jest.mock('../../../api/models/Projects');
jest.mock('../../../api/models/Inventories');
jest.mock('../../../api/models/ExecutionEnvironments');
jest.mock('../../../api/models/InstanceGroups');
jest.mock('../../../api/models/Root');

const mockJobTemplate = {
  allow_callbacks: false,
  allow_simultaneous: false,
  ask_scm_branch_on_launch: false,
  ask_diff_mode_on_launch: false,
  ask_variables_on_launch: false,
  ask_limit_on_launch: false,
  ask_tags_on_launch: false,
  ask_skip_tags_on_launch: false,
  ask_job_type_on_launch: false,
  ask_verbosity_on_launch: false,
  ask_inventory_on_launch: false,
  ask_credential_on_launch: false,
  ask_execution_environment_on_launch: false,
  ask_forks_on_launch: false,
  ask_instance_groups_on_launch: false,
  ask_job_slice_count_on_launch: false,
  ask_labels_on_launch: false,
  ask_timeout_on_launch: false,
  become_enabled: false,
  description: 'Bar',
  diff_mode: false,
  extra_vars: '---',
  forks: 0,
  host_config_key: '1234',
  id: 1,
  inventory: 2,
  job_slice_count: 1,
  job_tags: '',
  job_type: 'run',
  limit: '',
  name: 'Foo',
  playbook: 'Baz',
  project: 3,
  scm_branch: '',
  skip_tags: '',
  summary_fields: {
    execution_environment: {
      id: 1,
      name: 'Default EE',
      description: '',
      image: 'quay.io/ansible/awx-ee',
    },
    user_capabilities: {
      edit: true,
    },
    labels: {
      results: [
        { name: 'Sushi', id: 1 },
        { name: 'Major', id: 2 },
      ],
    },
    inventory: {
      id: 2,
      name: 'Demo Inventory',
      organization_id: 1,
    },
    credentials: [
      { id: 1, kind: 'cloud', name: 'Foo' },
      { id: 2, kind: 'ssh', name: 'Bar' },
    ],
    project: {
      id: 3,
      name: 'Boo',
    },
  },
  timeout: 0,
  type: 'job_template',
  use_fact_cache: false,
  verbosity: '0',
  webhook_credential: null,
  webhook_key: 'webhook Key',
  webhook_service: 'gitlab',
  related: {
    webhook_receiver: '/api/v2/workflow_job_templates/57/gitlab/',
  },
  execution_environment: 1,
};

const mockRelatedCredentials = {
  count: 2,
  next: null,
  previous: null,
  results: [
    {
      id: 1,
      type: 'credential',
      url: '/api/v2/credentials/1/',
      related: {},
      summary_fields: {
        user_capabilities: {
          edit: true,
          delete: true,
          copy: true,
          use: true,
        },
      },
      created: '2016-08-24T20:20:44.411607Z',
      modified: '2019-06-18T16:14:00.109434Z',
      name: 'Test Vault Credential',
      description: 'Credential with access to vaulted data.',
      organization: 1,
      credential_type: 3,
      inputs: { vault_password: '$encrypted$' },
    },
    {
      id: 2,
      type: 'credential',
      url: '/api/v2/credentials/2/',
      related: {},
      summary_fields: {
        user_capabilities: {
          edit: true,
          delete: true,
          copy: true,
          use: true,
        },
      },
      created: '2016-08-24T20:20:44.411607Z',
      modified: '2017-07-11T15:58:39.103659Z',
      name: 'Test Machine Credential',
      description: 'Credential with access to internal machines.',
      organization: 1,
      credential_type: 1,
      inputs: { ssh_key_data: '$encrypted$' },
    },
  ],
};

const mockRelatedProjectPlaybooks = [
  'check.yml',
  'debug-50.yml',
  'debug.yml',
  'debug2.yml',
  'debug_extra_vars.yml',
  'dynamic_inventory.yml',
  'environ_test.yml',
  'fail_unless.yml',
  'pass_unless.yml',
  'pause.yml',
  'ping-20.yml',
  'ping.yml',
  'setfact_50.yml',
  'vault.yml',
];

const mockInstanceGroups = [
  {
    id: 1,
    type: 'instance_group',
    url: '/api/v2/instance_groups/1/',
    related: {
      jobs: '/api/v2/instance_groups/1/jobs/',
      instances: '/api/v2/instance_groups/1/instances/',
    },
    name: 'tower',
    capacity: 59,
    committed_capacity: 0,
    consumed_capacity: 0,
    percent_capacity_remaining: 100.0,
    jobs_running: 0,
    jobs_total: 3,
    instances: 1,
    controller: null,
    policy_instance_percentage: 100,
    policy_instance_minimum: 0,
    policy_instance_list: [],
  },
];

const mockExecutionEnvironment = [
  {
    id: 1,
    name: 'Default EE',
    description: '',
    image: 'quay.io/ansible/awx-ee',
  },
];

describe('<JobTemplateEdit />', () => {
  beforeEach(() => {
    RootAPI.readAssetVariables.mockResolvedValue({
      data: {
        BRAND_NAME: 'AWX',
      },
    });
    JobTemplatesAPI.readCredentials.mockResolvedValue({
      data: mockRelatedCredentials,
    });
    JobTemplatesAPI.readInstanceGroups.mockReturnValue({
      data: { results: mockInstanceGroups },
    });

    InventoriesAPI.read.mockResolvedValue({
      data: {
        results: [],
        count: 0,
      },
    });
    InventoriesAPI.readOptions.mockResolvedValue({
      data: { actions: { GET: {}, POST: {} } },
    });

    InstanceGroupsAPI.read.mockResolvedValue({
      data: {
        results: [],
        count: 0,
      },
    });
    InstanceGroupsAPI.readOptions.mockResolvedValue({
      data: { actions: { GET: {}, POST: {} } },
    });

    ProjectsAPI.read.mockResolvedValue({
      data: {
        results: [],
        count: 0,
      },
    });
    ProjectsAPI.readOptions.mockResolvedValue({
      data: { actions: { GET: {}, POST: {} } },
    });
    ProjectsAPI.readPlaybooks.mockResolvedValue({
      data: mockRelatedProjectPlaybooks,
    });

    LabelsAPI.read.mockResolvedValue({ data: { results: [] } });

    CredentialsAPI.read.mockResolvedValue({
      data: {
        results: [],
        count: 0,
      },
    });
    CredentialsAPI.readOptions.mockResolvedValue({
      data: { actions: { GET: {}, POST: {} } },
    });

    CredentialTypesAPI.loadAllTypes.mockResolvedValue([]);

    ExecutionEnvironmentsAPI.read.mockResolvedValue({
      data: {
        results: mockExecutionEnvironment,
        count: 1,
      },
    });
    ExecutionEnvironmentsAPI.readOptions.mockResolvedValue({
      data: { actions: { GET: {}, POST: {} } },
    });

    useDebounce.mockImplementation((fn) => fn);
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  test('initially renders successfully', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <JobTemplateEdit template={mockJobTemplate} />
      );
    });
    wrapper.update();
    expect(wrapper.find('FormGroup[label="Host Config Key"]').length).toBe(1);
    expect(
      wrapper.find('FormGroup[label="Host Config Key"]').prop('isRequired')
    ).toBe(true);
  });

  test('handleSubmit should call api update', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <JobTemplateEdit
          template={mockJobTemplate}
          reloadTemplate={jest.fn()}
        />
      );
    });
    wrapper.update();

    const updatedTemplateData = {
      job_type: 'check',
      name: 'new name',
      inventory: {
        id: 1,
        name: 'Other Inventory',
      },
    };
    const labels = [
      { id: 3, name: 'Foo' },
      { id: 4, name: 'Bar' },
      { id: 5, name: 'Maple' },
      { id: 6, name: 'Tree' },
    ];
    await waitForElement(wrapper, 'LabelSelect', (el) => el.length > 0);
    act(() => {
      wrapper.find('LabelSelect').invoke('onChange')(labels);
      wrapper.update();
    });
    act(() => {
      wrapper.find('AnsibleSelect#template-job-type').prop('onChange')(
        null,
        'check'
      );
    });
    wrapper.update();
    act(() => {
      wrapper.find('InventoryLookup').invoke('onChange')({
        id: 1,
        name: 'Other Inventory',
      });

      wrapper.find('TextInput#execution-environments').invoke('onChange')('');
    });
    wrapper.update();

    wrapper.find('input#template-name').simulate('change', {
      target: { value: 'new name', name: 'name' },
    });

    await act(async () => {
      wrapper.find('button[aria-label="Save"]').simulate('click');
      wrapper.update();
    });

    const expected = {
      ...mockJobTemplate,
      ...updatedTemplateData,
      inventory: 1,
      project: 3,
      execution_environment: null,
    };
    delete expected.summary_fields;
    delete expected.id;
    delete expected.type;
    delete expected.related;
    delete expected.webhook_key;
    delete expected.webhook_url;
    expect(JobTemplatesAPI.update).toHaveBeenCalledWith(1, expected);
    expect(JobTemplatesAPI.disassociateLabel).toHaveBeenCalledTimes(2);
    expect(JobTemplatesAPI.associateLabel).toHaveBeenCalledTimes(4);
  });

  test('should navigate to job template detail when cancel is clicked', async () => {
    const history = createMemoryHistory({});
    let wrapper;
    let cancelButton;
    await act(async () => {
      wrapper = mountWithContexts(
        <JobTemplateEdit template={mockJobTemplate} />,
        { context: { router: { history } } }
      );
      cancelButton = await waitForElement(
        wrapper,
        'button[aria-label="Cancel"]',
        (e) => e.length === 1
      );
    });
    await act(async () => {
      cancelButton.prop('onClick')();
    });
    expect(history.location.pathname).toEqual(
      '/templates/job_template/1/details'
    );
  });
});
