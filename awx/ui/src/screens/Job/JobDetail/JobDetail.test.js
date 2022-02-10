import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { JobsAPI, ProjectUpdatesAPI } from 'api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import JobDetail from './JobDetail';
import mockJobData from '../shared/data.job.json';

jest.mock('../../../api');

describe('<JobDetail />', () => {
  let wrapper;
  function assertDetail(label, value) {
    expect(wrapper.find(`Detail[label="${label}"] dt`).text()).toBe(label);
    expect(wrapper.find(`Detail[label="${label}"] dd`).text()).toBe(value);
  }

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should display details', () => {
    wrapper = mountWithContexts(
      <JobDetail
        job={{
          ...mockJobData,
          summary_fields: {
            ...mockJobData.summary_fields,
            credential: {
              id: 2,
              name: 'Machine cred',
              description: '',
              kind: 'ssh',
              cloud: false,
              kubernetes: false,
              credential_type_id: 1,
            },
            source_workflow_job: {
              id: 1234,
              name: 'Test Source Workflow',
            },
          },
        }}
      />
    );

    // StatusIcon adds visibly hidden accessibility text " successful "
    assertDetail('Job ID', '2');
    assertDetail('Status', 'Successful');
    assertDetail('Started', '8/8/2019, 7:24:18 PM');
    assertDetail('Finished', '8/8/2019, 7:24:50 PM');
    assertDetail('Job Template', mockJobData.summary_fields.job_template.name);
    assertDetail('Source Workflow Job', `1234 - Test Source Workflow`);
    assertDetail('Job Type', 'Playbook Run');
    assertDetail('Launched By', mockJobData.summary_fields.created_by.username);
    assertDetail('Inventory', mockJobData.summary_fields.inventory.name);
    assertDetail('Project', mockJobData.summary_fields.project.name);
    assertDetail('Revision', mockJobData.scm_revision);
    assertDetail('Playbook', mockJobData.playbook);
    assertDetail('Verbosity', '0 (Normal)');
    assertDetail('Execution Node', mockJobData.execution_node);
    assertDetail(
      'Instance Group',
      mockJobData.summary_fields.instance_group.name
    );
    assertDetail('Job Slice', '0/1');
    assertDetail('Credentials', 'SSH: Demo Credential');
    assertDetail('Machine Credential', 'SSH: Machine cred');
    assertDetail('Source Control Branch', 'main');

    assertDetail(
      'Execution Environment',
      mockJobData.summary_fields.execution_environment.name
    );

    assertDetail('Job Slice', '0/1');

    const credentialChip = wrapper.find(
      `Detail[label="Credentials"] CredentialChip`
    );
    expect(credentialChip.prop('credential')).toEqual(
      mockJobData.summary_fields.credentials[0]
    );

    expect(
      wrapper
        .find('Detail[label="Job Tags"]')
        .containsAnyMatchingElements([<span>a</span>, <span>b</span>])
    ).toEqual(true);

    expect(
      wrapper
        .find('Detail[label="Skip Tags"]')
        .containsAnyMatchingElements([<span>c</span>, <span>d</span>])
    ).toEqual(true);

    const statusDetail = wrapper.find('Detail[label="Status"]');
    const statusLabel = statusDetail.find('StatusLabel');
    expect(statusLabel.prop('status')).toEqual('successful');

    const projectStatusDetail = wrapper.find('Detail[label="Project Status"]');
    expect(projectStatusDetail.find('StatusLabel')).toHaveLength(1);
    const projectStatusLabel = statusDetail.find('StatusLabel');
    expect(projectStatusLabel.prop('status')).toEqual('successful');
  });

  test('should not display finished date', () => {
    wrapper = mountWithContexts(
      <JobDetail
        job={{
          ...mockJobData,
          finished: null,
        }}
      />
    );
    expect(wrapper.find(`Detail[label="Finished"]`).length).toBe(0);
  });

  test('should display module name and module arguments', () => {
    wrapper = mountWithContexts(
      <JobDetail
        job={{
          ...mockJobData,
          type: 'ad_hoc_command',
          module_name: 'command',
          module_args: 'echo hello_world',
          summary_fields: {
            ...mockJobData.summary_fields,
            credential: {
              id: 2,
              name: 'Machine cred',
              description: '',
              kind: 'ssh',
              cloud: false,
              kubernetes: false,
              credential_type_id: 1,
            },
            source_workflow_job: {
              id: 1234,
              name: 'Test Source Workflow',
            },
          },
        }}
      />
    );
    assertDetail('Module Name', 'command');
    assertDetail('Module Arguments', 'echo hello_world');
    assertDetail('Job Type', 'Run Command');
  });

  test('should display source data', () => {
    wrapper = mountWithContexts(
      <JobDetail
        job={{
          ...mockJobData,
          source: 'scm',
          type: 'inventory_update',
          module_name: 'command',
          module_args: 'echo hello_world',
          summary_fields: {
            ...mockJobData.summary_fields,
            inventory_source: { id: 1, name: 'Inventory Source' },
            credential: {
              id: 2,
              name: 'Machine cred',
              description: '',
              kind: 'ssh',
              cloud: false,
              kubernetes: false,
              credential_type_id: 1,
            },
            source_workflow_job: {
              id: 1234,
              name: 'Test Source Workflow',
            },
          },
        }}
        inventorySourceLabels={[
          ['scm', 'Sourced from Project'],
          ['file', 'File, Directory or Script'],
        ]}
      />
    );
    assertDetail('Source', 'Sourced from Project');
  });

  test('should show schedule that launched workflow job', async () => {
    wrapper = mountWithContexts(
      <JobDetail
        job={{
          ...mockJobData,
          launch_type: 'scheduled',
          summary_fields: {
            user_capabilities: {},
            schedule: {
              name: 'mock wf schedule',
              id: 999,
            },
            unified_job_template: {
              unified_job_type: 'workflow_job',
              id: 888,
            },
          },
        }}
      />
    );
    const launchedByDetail = wrapper.find('Detail[label="Launched By"] dd');
    expect(launchedByDetail).toHaveLength(1);
    expect(launchedByDetail.text()).toBe('mock wf schedule');
    expect(
      launchedByDetail.find(
        'a[href="/templates/workflow_job_template/888/schedules/999/details"]'
      )
    ).toHaveLength(1);
  });

  test('should hide "Launched By" detail for JT launched from a workflow launched by a schedule', async () => {
    wrapper = mountWithContexts(
      <JobDetail
        job={{
          ...mockJobData,
          launch_type: 'workflow',
          type: 'job',
          summary_fields: {
            user_capabilities: {},
            source_workflow_job: {
              name: 'mock wf job',
              id: 888,
            },
            unified_job_template: {
              unified_job_type: 'job',
              id: 111,
            },
          },
        }}
      />
    );
    expect(wrapper.find('Detail[label="Launched By"] dt')).toHaveLength(0);
    expect(wrapper.find('Detail[label="Launched By"] dd')).toHaveLength(0);
  });

  test('should properly delete job', async () => {
    wrapper = mountWithContexts(<JobDetail job={mockJobData} />);
    wrapper.find('button[aria-label="Delete"]').simulate('click');
    wrapper.update();
    const modal = wrapper.find('Modal[aria-label="Alert modal"]');
    expect(modal.length).toBe(1);
    modal.find('button[aria-label="Confirm Delete"]').simulate('click');
    expect(JobsAPI.destroy).toHaveBeenCalledTimes(1);
  });

  test('should display error modal when a job does not delete properly', async () => {
    ProjectUpdatesAPI.destroy.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'delete',
            url: '/api/v2/project_updates/1',
          },
          data: 'An error occurred',
          status: 404,
        },
      })
    );
    wrapper = mountWithContexts(<JobDetail job={mockJobData} />);
    wrapper.find('button[aria-label="Delete"]').simulate('click');
    const modal = wrapper.find('Modal[aria-label="Alert modal"]');
    expect(modal.length).toBe(1);
    await act(async () => {
      modal.find('button[aria-label="Confirm Delete"]').simulate('click');
    });
    wrapper.update();

    const errorModal = wrapper.find('ErrorDetail');
    expect(errorModal.length).toBe(1);
  });

  test('should display Playbook Check detail', () => {
    wrapper = mountWithContexts(
      <JobDetail
        job={{
          ...mockJobData,
          job_type: 'check',
        }}
      />
    );
    assertDetail('Job Type', 'Playbook Check');
  });

  test('should not show cancel job button, not super user', () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/miscellaneous_system/edit'],
    });

    wrapper = mountWithContexts(
      <JobDetail
        job={{
          ...mockJobData,
          status: 'pending',
          type: 'system_job',
        }}
      />,
      {
        context: {
          router: {
            history,
          },
          config: {
            me: {
              is_superuser: false,
            },
          },
        },
      }
    );
    expect(
      wrapper.find('Button[aria-label="Cancel Demo Job Template"]')
    ).toHaveLength(0);
  });

  test('should not show cancel job button, job completed', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/miscellaneous_system/edit'],
    });

    wrapper = mountWithContexts(
      <JobDetail
        job={{
          ...mockJobData,
          status: 'success',
          type: 'project_update',
        }}
      />,
      {
        context: {
          router: {
            history,
          },
          config: {
            me: {
              is_superuser: true,
            },
          },
        },
      }
    );
    expect(
      wrapper.find('Button[aria-label="Cancel Demo Job Template"]')
    ).toHaveLength(0);
  });

  test('should show cancel button, pending, super user', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/miscellaneous_system/edit'],
    });

    wrapper = mountWithContexts(
      <JobDetail
        job={{
          ...mockJobData,
          status: 'pending',
          type: 'system_job',
        }}
      />,
      {
        context: {
          router: {
            history,
          },
          config: {
            me: {
              is_superuser: true,
            },
          },
        },
      }
    );
    expect(
      wrapper.find('Button[aria-label="Cancel Demo Job Template"]')
    ).toHaveLength(1);
  });

  test('should show cancel button, pending, super project update, not super user', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/miscellaneous_system/edit'],
    });

    wrapper = mountWithContexts(
      <JobDetail
        job={{
          ...mockJobData,
          status: 'pending',
          type: 'project_update',
        }}
      />,
      {
        context: {
          router: {
            history,
          },
          config: {
            me: {
              is_superuser: false,
            },
          },
        },
      }
    );
    expect(
      wrapper.find('Button[aria-label="Cancel Demo Job Template"]')
    ).toHaveLength(1);
  });

  test('should render workflow job details', () => {
    const workFlowJob = {
      id: 15,
      type: 'workflow_job',
      url: '/api/v2/workflow_jobs/15/',
      related: {
        created_by: '/api/v2/users/1/',
        modified_by: '/api/v2/users/1/',
        unified_job_template: '/api/v2/job_templates/9/',
        job_template: '/api/v2/job_templates/9/',
        workflow_nodes: '/api/v2/workflow_jobs/15/workflow_nodes/',
        labels: '/api/v2/workflow_jobs/15/labels/',
        activity_stream: '/api/v2/workflow_jobs/15/activity_stream/',
        relaunch: '/api/v2/workflow_jobs/15/relaunch/',
        cancel: '/api/v2/workflow_jobs/15/cancel/',
      },
      summary_fields: {
        organization: {
          id: 1,
          name: 'Default',
          description: '',
        },
        inventory: {
          id: 1,
          name: 'Demo Inventory',
          description: '',
          has_active_failures: false,
          total_hosts: 4,
          hosts_with_active_failures: 0,
          total_groups: 0,
          has_inventory_sources: false,
          total_inventory_sources: 0,
          inventory_sources_with_failures: 0,
          organization_id: 1,
          kind: '',
        },
        job_template: {
          id: 9,
          name: 'Sliced Job Template',
          description: '',
        },
        unified_job_template: {
          id: 9,
          name: 'Sliced Job Template',
          description: '',
          unified_job_type: 'job',
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
        user_capabilities: {
          delete: true,
          start: true,
        },
        labels: {
          count: 0,
          results: [],
        },
      },
      created: '2021-07-06T19:40:17.654030Z',
      modified: '2021-07-06T19:40:17.964699Z',
      name: 'Sliced Job Template',
      description: '',
      unified_job_template: 9,
      launch_type: 'manual',
      status: 'successful',
      failed: false,
      started: '2021-07-06T19:40:17.962019Z',
      finished: '2021-07-06T19:40:42.238563Z',
      canceled_on: null,
      elapsed: 24.277,
      job_explanation: '',
      launched_by: {
        id: 1,
        name: 'admin',
        type: 'user',
        url: '/api/v2/users/1/',
      },
      work_unit_id: null,
      workflow_job_template: null,
      extra_vars: '{}',
      allow_simultaneous: false,
      job_template: 9,
      is_sliced_job: true,
      inventory: 1,
      limit: '',
      scm_branch: '',
      webhook_service: '',
      webhook_credential: null,
      webhook_guid: '',
    };
    wrapper = mountWithContexts(<JobDetail job={workFlowJob} />);
    assertDetail('Status', 'Successful');
    assertDetail('Started', '7/6/2021, 7:40:17 PM');
    assertDetail('Finished', '7/6/2021, 7:40:42 PM');
    assertDetail('Job Template', 'Sliced Job Template');
    assertDetail('Job Type', 'Workflow Job');
    assertDetail('Inventory', 'Demo Inventory');
    assertDetail('Job Slice Parent', 'True');
  });
});
