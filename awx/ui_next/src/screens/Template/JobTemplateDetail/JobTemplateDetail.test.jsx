import React from 'react';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import JobTemplateDetail, { _JobTemplateDetail } from './JobTemplateDetail';
import { JobTemplatesAPI } from '@api';

jest.mock('@api');

describe('<JobTemplateDetail />', () => {
  const template = {
    forks: 1,
    host_config_key: 'ssh',
    name: 'Temp 1',
    job_type: 'run',
    inventory: 1,
    limit: '1',
    project: 7,
    playbook: '',
    id: 1,
    verbosity: 1,
    summary_fields: {
      user_capabilities: { edit: true },
      created_by: { username: 'Joe' },
      modified_by: { username: 'Joe' },
      credentials: [
        { id: 1, kind: 'ssh', name: 'Credential 1' },
        { id: 2, kind: 'awx', name: 'Credential 2' },
      ],
      inventory: { name: 'Inventory' },
      project: { name: 'Project' },
    },
  };

  const mockInstanceGroups = {
    count: 5,
    data: {
      results: [{ id: 1, name: 'IG1' }, { id: 2, name: 'IG2' }],
    },
  };

  const readInstanceGroups = jest.spyOn(
    _JobTemplateDetail.prototype,
    'readInstanceGroups'
  );

  beforeEach(() => {
    JobTemplatesAPI.readInstanceGroups.mockResolvedValue(mockInstanceGroups);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('Can load with missing summary fields', async () => {
    const mockTemplate = { ...template };
    mockTemplate.summary_fields = { user_capabilities: {} };

    const wrapper = mountWithContexts(
      <JobTemplateDetail template={mockTemplate} />
    );
    await waitForElement(
      wrapper,
      'Detail[label="Description"]',
      el => el.length === 1
    );
  });

  test('When component mounts API is called to get instance groups', async done => {
    const wrapper = mountWithContexts(
      <JobTemplateDetail template={template} />
    );
    await waitForElement(
      wrapper,
      'JobTemplateDetail',
      el => el.state('hasContentLoading') === true
    );
    expect(readInstanceGroups).toHaveBeenCalled();
    await waitForElement(
      wrapper,
      'JobTemplateDetail',
      el => el.state('hasContentLoading') === false
    );
    expect(JobTemplatesAPI.readInstanceGroups).toHaveBeenCalledTimes(1);
    done();
  });

  test('Edit button is absent when user does not have edit privilege', async done => {
    const regularUser = {
      forks: 1,
      host_config_key: 'ssh',
      name: 'Temp 1',
      job_tags: 'cookies,pizza',
      job_type: 'run',
      inventory: 1,
      limit: '1',
      project: 7,
      playbook: '',
      id: 1,
      verbosity: 0,
      created_by: 'Alex',
      skip_tags: 'coffe,tea',
      summary_fields: {
        user_capabilities: { edit: false },
        created_by: { username: 'Joe' },
        modified_by: { username: 'Joe' },
        inventory: { name: 'Inventory' },
        project: { name: 'Project' },
        labels: { count: 1, results: [{ name: 'Label', id: 1 }] },
      },
    };
    const wrapper = mountWithContexts(
      <JobTemplateDetail template={regularUser} />
    );
    const jobTemplateDetail = wrapper.find('JobTemplateDetail');
    const editButton = jobTemplateDetail.find('button[aria-label="Edit"]');

    jobTemplateDetail.setState({
      instanceGroups: mockInstanceGroups,
      hasContentLoading: false,
      contentError: false,
    });
    expect(editButton.length).toBe(0);
    done();
  });

  test('should render CredentialChip', () => {
    template.summary_fields.credentials = [{ id: 1, name: 'cred', kind: null }];
    const wrapper = mountWithContexts(
      <JobTemplateDetail template={template} />
    );
    wrapper.find('JobTemplateDetail').setState({
      instanceGroups: mockInstanceGroups,
      hasContentLoading: false,
      contentError: false,
    });

    const chip = wrapper.find('CredentialChip');
    expect(chip).toHaveLength(1);
    expect(chip.prop('credential')).toEqual(
      template.summary_fields.credentials[0]
    );
  });
});
