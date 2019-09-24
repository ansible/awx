import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import { sleep } from '@testUtils/testUtils';
import JobDetail from './JobDetail';
import { JobsAPI, ProjectUpdatesAPI } from '@api';
import mockJobData from '../shared/data.job.json';

jest.mock('@api');

describe('<JobDetail />', () => {
  test('initially renders succesfully', () => {
    mountWithContexts(<JobDetail job={mockJobData} />);
  });

  test('should display a Close button', () => {
    const wrapper = mountWithContexts(<JobDetail job={mockJobData} />);

    expect(wrapper.find('Button[aria-label="close"]').length).toBe(1);
    wrapper.unmount();
  });

  test('should display details', () => {
    const wrapper = mountWithContexts(<JobDetail job={mockJobData} />);

    function assertDetail(label, value) {
      expect(wrapper.find(`Detail[label="${label}"] dt`).text()).toBe(label);
      expect(wrapper.find(`Detail[label="${label}"] dd`).text()).toBe(value);
    }

    assertDetail('Status', 'Successful');
    assertDetail('Started', mockJobData.started);
    assertDetail('Finished', mockJobData.finished);
    assertDetail('Template', mockJobData.summary_fields.job_template.name);
    assertDetail('Job Type', 'Run');
    assertDetail('Launched By', mockJobData.summary_fields.created_by.username);
    assertDetail('Inventory', mockJobData.summary_fields.inventory.name);
    assertDetail('Project', mockJobData.summary_fields.project.name);
    assertDetail('Revision', mockJobData.scm_revision);
    assertDetail('Playbook', mockJobData.playbook);
    assertDetail('Verbosity', '0 (Normal)');
    assertDetail('Environment', mockJobData.custom_virtualenv);
    assertDetail('Execution Node', mockJobData.execution_node);
    assertDetail(
      'Instance Group',
      mockJobData.summary_fields.instance_group.name
    );
    assertDetail('Job Slice', '0/1');
    assertDetail('Credentials', 'SSH: Demo Credential');
  });

  test('should display credentials', () => {
    const wrapper = mountWithContexts(<JobDetail job={mockJobData} />);
    const credentialChip = wrapper.find('CredentialChip');

    expect(credentialChip.prop('credential')).toEqual(
      mockJobData.summary_fields.credentials[0]
    );
  });

  test('should display successful job status icon', () => {
    const wrapper = mountWithContexts(<JobDetail job={mockJobData} />);
    const statusDetail = wrapper.find('Detail[label="Status"]');
    expect(statusDetail.find('StatusIcon__SuccessfulTop')).toHaveLength(1);
    expect(statusDetail.find('StatusIcon__SuccessfulBottom')).toHaveLength(1);
  });

  test('should display successful project status icon', () => {
    const wrapper = mountWithContexts(<JobDetail job={mockJobData} />);
    const statusDetail = wrapper.find('Detail[label="Project"]');
    expect(statusDetail.find('StatusIcon__SuccessfulTop')).toHaveLength(1);
    expect(statusDetail.find('StatusIcon__SuccessfulBottom')).toHaveLength(1);
  });

  test('should properly delete job', async () => {
    job = {
      name: 'Rage',
      id: 1,
      type: 'job',
      summary_fields: {
        job_template: { name: 'Spud' },
      },
    };
    const wrapper = mountWithContexts(<JobDetail job={job} />);
    wrapper
      .find('button')
      .at(0)
      .simulate('click');
    await sleep(1);
    wrapper.update();
    const modal = wrapper.find('Modal');
    expect(modal.length).toBe(1);
    modal.find('button[aria-label="Delete"]').simulate('click');
    expect(JobsAPI.destroy).toHaveBeenCalledTimes(1);
  });
  // The test below is skipped until react can be upgraded to at least 16.9.0.  An upgrade to
  // react - router will likely be necessary also.
  test.skip('should display error modal when a job does not delete properly', async () => {
    job = {
      name: 'Angry',
      id: 'a',
      type: 'project_update',
      summary_fields: {
        job_template: { name: 'Peanut' },
      },
    };
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
    const wrapper = mountWithContexts(<JobDetail job={job} />);

    wrapper
      .find('button')
      .at(0)
      .simulate('click');
    const modal = wrapper.find('Modal');
    await act(async () => {
      await modal.find('Button[variant="danger"]').prop('onClick')();
    });
    wrapper.update();

    const errorModal = wrapper.find('ErrorDetail');
    expect(errorModal.length).toBe(1);
  });
});
