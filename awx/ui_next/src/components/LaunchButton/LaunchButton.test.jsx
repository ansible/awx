import React from 'react';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import { sleep } from '../../../testUtils/testUtils';

import LaunchButton from './LaunchButton';
import { JobTemplatesAPI, WorkflowJobTemplatesAPI } from '../../api';

jest.mock('../../api/models/WorkflowJobTemplates');
jest.mock('../../api/models/JobTemplates');

describe('LaunchButton', () => {
  JobTemplatesAPI.readLaunch.mockResolvedValue({
    data: {
      can_start_without_user_input: true,
      ask_inventory_on_launch: false,
      ask_variables_on_launch: false,
      ask_limit_on_launch: false,
      ask_scm_branch_on_launch: false,
      survey_enabled: false,
      variables_needed_to_start: [],
    },
  });

  const children = ({ handleLaunch }) => (
    <button type="submit" onClick={() => handleLaunch()} />
  );

  const resource = {
    id: 1,
    type: 'job_template',
  };

  afterEach(() => jest.clearAllMocks());

  test('renders the expected content', () => {
    const wrapper = mountWithContexts(
      <LaunchButton resource={resource}>{children}</LaunchButton>
    );
    expect(wrapper).toHaveLength(1);
  });

  test('should redirect to job after successful launch', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/jobs/9000'],
    });

    JobTemplatesAPI.launch.mockResolvedValue({
      data: {
        id: 9000,
      },
    });
    const wrapper = mountWithContexts(
      <LaunchButton resource={resource}>{children}</LaunchButton>,
      {
        context: {
          router: { history },
        },
      }
    );
    const button = wrapper.find('button');
    button.prop('onClick')();
    expect(JobTemplatesAPI.readLaunch).toHaveBeenCalledWith(1);
    await sleep(0);
    expect(JobTemplatesAPI.launch).toHaveBeenCalledWith(1, {});
    expect(history.location.pathname).toEqual('/jobs/9000/output');
  });

  test('should launch the correct job type', async () => {
    WorkflowJobTemplatesAPI.readLaunch.mockResolvedValue({
      data: {
        can_start_without_user_input: true,
      },
    });
    const history = createMemoryHistory({
      initialEntries: ['/jobs/9000'],
    });
    WorkflowJobTemplatesAPI.launch.mockResolvedValue({
      data: {
        id: 9000,
      },
    });
    const wrapper = mountWithContexts(
      <LaunchButton
        resource={{
          id: 1,
          type: 'workflow_job_template',
        }}
      >
        {children}
      </LaunchButton>,
      {
        context: {
          router: { history },
        },
      }
    );
    const button = wrapper.find('button');
    button.prop('onClick')();
    expect(WorkflowJobTemplatesAPI.readLaunch).toHaveBeenCalledWith(1);
    await sleep(0);
    expect(WorkflowJobTemplatesAPI.launch).toHaveBeenCalledWith(1, {});
    expect(history.location.pathname).toEqual('/jobs/workflow/9000/output');
  });

  test('displays error modal after unsuccessful launch', async () => {
    const wrapper = mountWithContexts(
      <LaunchButton resource={resource}>{children}</LaunchButton>
    );
    JobTemplatesAPI.launch.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'post',
            url: '/api/v2/job_templates/1/launch',
          },
          data: 'An error occurred',
          status: 403,
        },
      })
    );
    expect(wrapper.find('Modal').length).toBe(0);
    wrapper.find('button').prop('onClick')();
    await sleep(0);
    wrapper.update();
    expect(wrapper.find('Modal').length).toBe(1);
    wrapper.find('ModalBoxCloseButton').simulate('click');
    await sleep(0);
    wrapper.update();
    expect(wrapper.find('Modal').length).toBe(0);
  });
});
