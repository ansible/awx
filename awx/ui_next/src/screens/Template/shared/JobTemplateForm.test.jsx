import React from 'react';
import { act } from 'react-dom/test-utils';
import { Route } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import { sleep } from '../../../../testUtils/testUtils';
import JobTemplateForm from './JobTemplateForm';
import {
  LabelsAPI,
  JobTemplatesAPI,
  ProjectsAPI,
  CredentialsAPI,
  CredentialTypesAPI,
  InventoriesAPI,
} from '../../../api';

jest.mock('../../../api');

describe('<JobTemplateForm />', () => {
  const mockData = {
    id: 1,
    name: 'Foo',
    description: 'Bar',
    job_type: 'run',
    inventory: 2,
    project: 3,
    playbook: 'Baz',
    type: 'job_template',
    scm_branch: 'Foo',
    limit: '5000',
    summary_fields: {
      inventory: {
        id: 2,
        name: 'foo',
        organization_id: 1,
      },
      project: {
        id: 3,
        name: 'qux',
      },
      labels: {
        results: [
          { name: 'Sushi', id: 1 },
          { name: 'Major', id: 2 },
        ],
      },
      credentials: [
        { id: 1, kind: 'cloud', name: 'Foo' },
        { id: 2, kind: 'ssh', name: 'Bar' },
      ],
    },
    related: { webhook_receiver: '/api/v2/job_templates/57/gitlab/' },
    webhook_key: 'webhook key',
    webhook_service: 'github',
    webhook_credential: 7,
    host_config_key: '',
  };
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
  const mockCredentials = [
    { id: 1, kind: 'cloud', name: 'Cred 1', url: 'www.google.com' },
    { id: 2, kind: 'ssh', name: 'Cred 2', url: 'www.google.com' },
    { id: 3, kind: 'Ansible', name: 'Cred 3', url: 'www.google.com' },
    { id: 4, kind: 'Machine', name: 'Cred 4', url: 'www.google.com' },
    { id: 5, kind: 'Machine', name: 'Cred 5', url: 'www.google.com' },
  ];

  beforeAll(() => {
    jest.setTimeout(5000 * 4);
  });

  afterAll(() => {
    jest.setTimeout(5000);
  });

  beforeEach(() => {
    LabelsAPI.read.mockReturnValue({
      data: mockData.summary_fields.labels,
    });
    CredentialTypesAPI.loadAllTypes.mockResolvedValue([]);
    CredentialsAPI.read.mockReturnValue({
      data: { results: mockCredentials },
    });
    JobTemplatesAPI.readInstanceGroups.mockReturnValue({
      data: { results: mockInstanceGroups },
    });
    JobTemplatesAPI.updateWebhookKey.mockReturnValue({
      data: { webhook_key: 'webhook key' },
    });
    JobTemplatesAPI.updateWebhookKey.mockReturnValue({
      data: { webhook_key: 'webhook key' },
    });
    ProjectsAPI.readDetail.mockReturnValue({
      name: 'foo',
      id: 1,
      allow_override: true,
    });
    ProjectsAPI.readPlaybooks.mockReturnValue({
      data: ['debug.yml'],
    });
    InventoriesAPI.readOptions.mockResolvedValue({
      data: { actions: { GET: {}, POST: {} } },
    });
    ProjectsAPI.readOptions.mockResolvedValue({
      data: { actions: { GET: {}, POST: {} } },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should render LabelsSelect', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <JobTemplateForm
          template={mockData}
          handleSubmit={jest.fn()}
          handleCancel={jest.fn()}
        />
      );
    });
    expect(LabelsAPI.read).toHaveBeenCalled();
    expect(JobTemplatesAPI.readInstanceGroups).toHaveBeenCalled();
    wrapper.update();
    const select = wrapper.find('LabelSelect');
    expect(select).toHaveLength(1);
    expect(select.prop('value')).toEqual(
      mockData.summary_fields.labels.results
    );
  });

  test('should update form values on input changes', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <JobTemplateForm
          template={mockData}
          handleSubmit={jest.fn()}
          handleCancel={jest.fn()}
        />
      );
    });
    await waitForElement(wrapper, 'EmptyStateBody', el => el.length === 0);
    await act(async () => {
      wrapper.find('input#template-name').simulate('change', {
        target: { value: 'new foo', name: 'name' },
      });
      wrapper.find('input#template-description').simulate('change', {
        target: { value: 'new bar', name: 'description' },
      });
      wrapper.find('AnsibleSelect#template-job-type').prop('onChange')(
        null,
        'check'
      );
      wrapper.find('ProjectLookup').invoke('onChange')({
        id: 4,
        name: 'project',
        allow_override: true,
      });
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('InventoryLookup').invoke('onChange')({
        id: 3,
        name: 'inventory',
      });
    });

    wrapper.update();
    await act(async () => {
      wrapper.find('TextInputBase#template-scm-branch').prop('onChange')(
        'devel'
      );
      wrapper.find('TextInputBase#template-limit').prop('onChange')(1234567890);
      wrapper.find('AnsibleSelect[name="playbook"]').simulate('change', {
        target: { value: 'new baz type', name: 'playbook' },
      });
    });

    await act(async () => {
      wrapper
        .find('CredentialChip')
        .at(0)
        .prop('onClick')();
    });
    wrapper.update();

    expect(wrapper.find('input#template-name').prop('value')).toEqual(
      'new foo'
    );
    expect(wrapper.find('input#template-description').prop('value')).toEqual(
      'new bar'
    );
    expect(
      wrapper.find('AnsibleSelect[name="job_type"]').prop('value')
    ).toEqual('check');
    expect(wrapper.find('InventoryLookup').prop('value')).toEqual({
      id: 3,
      name: 'inventory',
    });
    expect(wrapper.find('ProjectLookup').prop('value')).toEqual({
      id: 4,
      name: 'project',
      allow_override: true,
    });
    expect(wrapper.find('input#template-scm-branch').prop('value')).toEqual(
      'devel'
    );
    expect(wrapper.find('input#template-limit').prop('value')).toEqual(
      1234567890
    );
    expect(
      wrapper.find('AnsibleSelect[name="playbook"]').prop('value')
    ).toEqual('new baz type');
    expect(wrapper.find('MultiCredentialsLookup').prop('value')).toEqual([
      {
        id: 2,
        kind: 'ssh',
        name: 'Bar',
      },
    ]);
  });

  test('webhooks and enable concurrent jobs functions properly', async () => {
    let wrapper;
    const history = createMemoryHistory({
      initialEntries: ['/templates/job_template/1/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Route
          path="/templates/job_template/:id/edit"
          component={() => (
            <JobTemplateForm
              template={mockData}
              handleSubmit={jest.fn()}
              handleCancel={jest.fn()}
            />
          )}
        />,
        {
          context: {
            router: {
              history,
              route: {
                location: history.location,
                match: { params: { id: 1 } },
              },
            },
          },
        }
      );
    });
    act(() => {
      wrapper.find('Checkbox[aria-label="Enable Webhook"]').invoke('onChange')(
        true,
        {
          currentTarget: { value: true, type: 'change', checked: true },
        }
      );
    });
    wrapper.update();
    expect(
      wrapper.find('Checkbox[aria-label="Enable Webhook"]').prop('isChecked')
    ).toBe(true);

    expect(
      wrapper.find('input[aria-label="wfjt-webhook-key"]').prop('readOnly')
    ).toBe(true);
    expect(
      wrapper.find('input[aria-label="wfjt-webhook-key"]').prop('value')
    ).toBe('webhook key');
    await act(() =>
      wrapper.find('Button[aria-label="Update webhook key"]').prop('onClick')()
    );
    expect(JobTemplatesAPI.updateWebhookKey).toBeCalledWith('1');
    expect(
      wrapper.find('TextInputBase[aria-label="Webhook URL"]').prop('value')
    ).toContain('/api/v2/job_templates/57/gitlab/');

    wrapper.update();

    expect(wrapper.find('FormGroup[name="webhook_service"]').length).toBe(1);

    await act(async () =>
      wrapper.find('AnsibleSelect#webhook_service').prop('onChange')(
        {},
        'gitlab'
      )
    );
    wrapper.update();

    expect(wrapper.find('AnsibleSelect#webhook_service').prop('value')).toBe(
      'gitlab'
    );
  });

  test('webhooks should render properly, without data', async () => {
    let wrapper;
    const history = createMemoryHistory({
      initialEntries: ['/templates/job_template/1/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Route
          path="/templates/job_template/:id/edit"
          component={() => (
            <JobTemplateForm
              template={{
                ...mockData,
                webhook_credential: null,
                webhook_key: '',
                webhook_service: 'github',
                related: { webhook_receiver: '' },
              }}
              handleSubmit={jest.fn()}
              handleCancel={jest.fn()}
            />
          )}
        />,
        {
          context: {
            router: {
              history,
              route: {
                location: history.location,
                match: { params: { id: 1 } },
              },
            },
          },
        }
      );
    });
    expect(
      wrapper.find('TextInputBase#template-webhook_key').prop('value')
    ).toBe('A NEW WEBHOOK KEY WILL BE GENERATED ON SAVE.');
    expect(
      wrapper.find('Button[aria-label="Update webhook key"]').prop('isDisabled')
    ).toBe(true);
  });
  test('should call handleSubmit when Submit button is clicked', async () => {
    const handleSubmit = jest.fn();
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <JobTemplateForm
          template={mockData}
          handleSubmit={handleSubmit}
          handleCancel={jest.fn()}
        />
      );
    });
    await waitForElement(wrapper, 'EmptyStateBody', el => el.length === 0);
    expect(handleSubmit).not.toHaveBeenCalled();
    await act(async () => {
      wrapper.find('button[aria-label="Save"]').simulate('click');
    });
    await sleep(1);
    expect(handleSubmit).toBeCalled();
  });

  test('should call handleCancel when Cancel button is clicked', async () => {
    const handleCancel = jest.fn();
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <JobTemplateForm
          template={mockData}
          handleSubmit={jest.fn()}
          handleCancel={handleCancel}
        />
      );
    });
    await waitForElement(wrapper, 'EmptyStateBody', el => el.length === 0);
    expect(handleCancel).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    expect(handleCancel).toBeCalled();
  });
});
