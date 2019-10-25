import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { sleep } from '@testUtils/testUtils';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import { JobTemplatesAPI, LabelsAPI, ProjectsAPI } from '@api';
import JobTemplateEdit from './JobTemplateEdit';

jest.mock('@api');

const mockJobTemplate = {
  id: 1,
  name: 'Foo',
  description: 'Bar',
  job_type: 'run',
  inventory: 2,
  project: 3,
  playbook: 'Baz',
  type: 'job_template',
  forks: 0,
  limit: '',
  verbosity: '0',
  job_slice_count: 1,
  timeout: 0,
  job_tags: '',
  skip_tags: '',
  diff_mode: false,
  allow_callbacks: false,
  allow_simultaneous: false,
  use_fact_cache: false,
  host_config_key: '',
  summary_fields: {
    user_capabilities: {
      edit: true,
    },
    labels: {
      results: [{ name: 'Sushi', id: 1 }, { name: 'Major', id: 2 }],
    },
    inventory: {
      id: 2,
      organization_id: 1,
    },
    credentials: [
      { id: 1, kind: 'cloud', name: 'Foo' },
      { id: 2, kind: 'ssh', name: 'Bar' },
    ],
  },
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
    is_controller: false,
    is_isolated: false,
    policy_instance_percentage: 100,
    policy_instance_minimum: 0,
    policy_instance_list: [],
  },
];

JobTemplatesAPI.readCredentials.mockResolvedValue({
  data: mockRelatedCredentials,
});
ProjectsAPI.readPlaybooks.mockResolvedValue({
  data: mockRelatedProjectPlaybooks,
});
LabelsAPI.read.mockResolvedValue({ data: { results: [] } });

describe('<JobTemplateEdit />', () => {
  beforeEach(() => {
    LabelsAPI.read.mockResolvedValue({ data: { results: [] } });
    JobTemplatesAPI.readCredentials.mockResolvedValue({
      data: mockRelatedCredentials,
    });
    JobTemplatesAPI.readInstanceGroups.mockReturnValue({
      data: { results: mockInstanceGroups },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('initially renders successfully', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <JobTemplateEdit template={mockJobTemplate} />
      );
    });
    await waitForElement(wrapper, 'EmptyStateBody', el => el.length === 0);
  });

  test('handleSubmit should call api update', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <JobTemplateEdit template={mockJobTemplate} />
      );
    });
    await waitForElement(wrapper, 'JobTemplateForm', e => e.length === 1);
    const updatedTemplateData = {
      name: 'new name',
      description: 'new description',
      job_type: 'check',
    };
    const labels = [
      { id: 3, name: 'Foo', isNew: true },
      { id: 4, name: 'Bar', isNew: true },
      { id: 5, name: 'Maple' },
      { id: 6, name: 'Tree' },
    ];
    JobTemplatesAPI.update.mockResolvedValue({
      data: { ...updatedTemplateData },
    });
    const formik = wrapper.find('Formik').instance();
    const changeState = new Promise(resolve => {
      const values = {
        ...mockJobTemplate,
        ...updatedTemplateData,
        labels,
        instanceGroups: [],
      };
      formik.setState({ values }, () => resolve());
    });
    await changeState;
    wrapper.find('button[aria-label="Save"]').simulate('click');
    await sleep(0);

    expect(JobTemplatesAPI.update).toHaveBeenCalledWith(1, {
      ...mockJobTemplate,
      ...updatedTemplateData,
    });
    expect(JobTemplatesAPI.disassociateLabel).toHaveBeenCalledTimes(2);
    expect(JobTemplatesAPI.associateLabel).toHaveBeenCalledTimes(2);
    expect(JobTemplatesAPI.generateLabel).toHaveBeenCalledTimes(2);
  });

  test('should navigate to job template detail when cancel is clicked', async () => {
    const history = createMemoryHistory({});
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <JobTemplateEdit template={mockJobTemplate} />,
        { context: { router: { history } } }
      );
    });
    const cancelButton = await waitForElement(
      wrapper,
      'button[aria-label="Cancel"]',
      e => e.length === 1
    );
    cancelButton.prop('onClick')();
    expect(history.location.pathname).toEqual(
      '/templates/job_template/1/details'
    );
  });
});
