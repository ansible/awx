import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import { sleep } from '@testUtils/testUtils';
import JobTemplateForm from './JobTemplateForm';
import { LabelsAPI, JobTemplatesAPI, ProjectsAPI, CredentialsAPI } from '@api';

jest.mock('@api');

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
      labels: { results: [{ name: 'Sushi', id: 1 }, { name: 'Major', id: 2 }] },
      credentials: [
        { id: 1, kind: 'cloud', name: 'Foo' },
        { id: 2, kind: 'ssh', name: 'Bar' },
      ],
    },
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

  beforeEach(() => {
    LabelsAPI.read.mockReturnValue({
      data: mockData.summary_fields.labels,
    });
    CredentialsAPI.read.mockReturnValue({
      data: { results: mockCredentials },
    });
    JobTemplatesAPI.readInstanceGroups.mockReturnValue({
      data: { results: mockInstanceGroups },
    });
    ProjectsAPI.readPlaybooks.mockReturnValue({
      data: ['debug.yml'],
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
    const form = wrapper.find('Formik');
    wrapper.find('input#template-name').simulate('change', {
      target: { value: 'new foo', name: 'name' },
    });
    expect(form.state('values').name).toEqual('new foo');
    wrapper.find('input#template-description').simulate('change', {
      target: { value: 'new bar', name: 'description' },
    });
    expect(form.state('values').description).toEqual('new bar');
    wrapper.find('AnsibleSelect[name="job_type"]').simulate('change', {
      target: { value: 'new job type', name: 'job_type' },
    });
    expect(form.state('values').job_type).toEqual('new job type');
    wrapper.find('InventoryLookup').invoke('onChange')({
      id: 3,
      name: 'inventory',
    });
    expect(form.state('values').inventory).toEqual(3);
    await act(async () => {
      wrapper.find('ProjectLookup').invoke('onChange')({
        id: 4,
        name: 'project',
      });
    });
    expect(form.state('values').project).toEqual(4);
    wrapper.find('AnsibleSelect[name="playbook"]').simulate('change', {
      target: { value: 'new baz type', name: 'playbook' },
    });
    expect(form.state('values').playbook).toEqual('new baz type');
    wrapper
      .find('CredentialChip')
      .at(0)
      .prop('onClick')();
    expect(form.state('values').credentials).toEqual([
      { id: 2, kind: 'ssh', name: 'Bar' },
    ]);
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
    wrapper.find('button[aria-label="Save"]').simulate('click');
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
