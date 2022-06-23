import React from 'react';
import { createMemoryHistory } from 'history';
import { act } from 'react-dom/test-utils';
import {
  InventorySourcesAPI,
  JobsAPI,
  JobTemplatesAPI,
  ProjectsAPI,
  WorkflowJobsAPI,
  WorkflowJobTemplatesAPI,
} from 'api';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import LaunchButton from './LaunchButton';

jest.mock('../../api');

describe('LaunchButton', () => {
  const launchButton = ({ handleLaunch }) => (
    <button type="submit" onClick={() => handleLaunch()} />
  );

  const relaunchButton = ({ handleRelaunch }) => (
    <button type="submit" onClick={() => handleRelaunch()} />
  );

  const resource = {
    id: 1,
    type: 'job_template',
  };

  beforeEach(() => {
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
  });

  afterEach(() => jest.clearAllMocks());

  test('renders the expected content', () => {
    const wrapper = mountWithContexts(
      <LaunchButton resource={resource}>{launchButton}</LaunchButton>
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
      <LaunchButton resource={resource}>{launchButton}</LaunchButton>,
      {
        context: {
          router: { history },
        },
      }
    );
    const button = wrapper.find('button');
    await act(() => button.prop('onClick')());
    expect(JobTemplatesAPI.readLaunch).toHaveBeenCalledWith(1);
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
        {launchButton}
      </LaunchButton>,
      {
        context: {
          router: { history },
        },
      }
    );
    const button = wrapper.find('button');
    await act(() => button.prop('onClick')());
    expect(WorkflowJobTemplatesAPI.readLaunch).toHaveBeenCalledWith(1);
    expect(WorkflowJobTemplatesAPI.launch).toHaveBeenCalledWith(1, {});
    expect(history.location.pathname).toEqual('/jobs/9000/output');
  });

  test('should relaunch job correctly', async () => {
    JobsAPI.readRelaunch.mockResolvedValue({
      data: {
        can_start_without_user_input: true,
      },
    });
    const history = createMemoryHistory({
      initialEntries: ['/jobs/9000'],
    });
    JobsAPI.relaunch.mockResolvedValue({
      data: {
        id: 9000,
      },
    });
    const wrapper = mountWithContexts(
      <LaunchButton
        resource={{
          id: 1,
          type: 'job',
        }}
      >
        {relaunchButton}
      </LaunchButton>,
      {
        context: {
          router: { history },
        },
      }
    );
    const button = wrapper.find('button');
    await act(() => button.prop('onClick')());
    expect(JobsAPI.readRelaunch).toHaveBeenCalledWith(1);
    expect(JobsAPI.relaunch).toHaveBeenCalledWith(1, {});
    expect(history.location.pathname).toEqual('/jobs/9000/output');
  });

  test('should relaunch workflow job correctly', async () => {
    WorkflowJobsAPI.readRelaunch.mockResolvedValue({
      data: {
        can_start_without_user_input: true,
      },
    });
    const history = createMemoryHistory({
      initialEntries: ['/jobs/9000'],
    });
    WorkflowJobsAPI.relaunch.mockResolvedValue({
      data: {
        id: 9000,
      },
    });
    const wrapper = mountWithContexts(
      <LaunchButton
        resource={{
          id: 1,
          type: 'workflow_job',
        }}
      >
        {relaunchButton}
      </LaunchButton>,
      {
        context: {
          router: { history },
        },
      }
    );
    const button = wrapper.find('button');
    await act(() => button.prop('onClick')());
    expect(WorkflowJobsAPI.readRelaunch).toHaveBeenCalledWith(1);
    expect(WorkflowJobsAPI.relaunch).toHaveBeenCalledWith(1);
    expect(history.location.pathname).toEqual('/jobs/9000/output');
  });

  test('should relaunch project sync correctly', async () => {
    ProjectsAPI.readLaunchUpdate.mockResolvedValue({
      data: {
        can_start_without_user_input: true,
      },
    });
    const history = createMemoryHistory({
      initialEntries: ['/jobs/9000'],
    });
    ProjectsAPI.launchUpdate.mockResolvedValue({
      data: {
        id: 9000,
      },
    });
    const wrapper = mountWithContexts(
      <LaunchButton
        resource={{
          id: 1,
          project: 5,
          type: 'project_update',
        }}
      >
        {relaunchButton}
      </LaunchButton>,
      {
        context: {
          router: { history },
        },
      }
    );
    const button = wrapper.find('button');
    await act(() => button.prop('onClick')());
    expect(ProjectsAPI.readLaunchUpdate).toHaveBeenCalledWith(5);
    expect(ProjectsAPI.launchUpdate).toHaveBeenCalledWith(5);
    expect(history.location.pathname).toEqual('/jobs/9000/output');
  });

  test('should relaunch project sync correctly', async () => {
    InventorySourcesAPI.readLaunchUpdate.mockResolvedValue({
      data: {
        can_start_without_user_input: true,
      },
    });
    const history = createMemoryHistory({
      initialEntries: ['/jobs/9000'],
    });
    InventorySourcesAPI.launchUpdate.mockResolvedValue({
      data: {
        id: 9000,
      },
    });
    const wrapper = mountWithContexts(
      <LaunchButton
        resource={{
          id: 1,
          inventory_source: 5,
          type: 'inventory_update',
        }}
      >
        {relaunchButton}
      </LaunchButton>,
      {
        context: {
          router: { history },
        },
      }
    );
    const button = wrapper.find('button');
    await act(() => button.prop('onClick')());
    expect(InventorySourcesAPI.readLaunchUpdate).toHaveBeenCalledWith(5);
    expect(InventorySourcesAPI.launchUpdate).toHaveBeenCalledWith(5);
    expect(history.location.pathname).toEqual('/jobs/9000/output');
  });

  test('displays error modal after unsuccessful launch', async () => {
    const wrapper = mountWithContexts(
      <LaunchButton resource={resource}>{launchButton}</LaunchButton>
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
    await act(() => wrapper.find('button').prop('onClick')());
    wrapper.update();
    expect(wrapper.find('Modal').length).toBe(1);
    wrapper.find('ModalBoxCloseButton').simulate('click');
    wrapper.update();
    expect(wrapper.find('Modal').length).toBe(0);
  });
});
