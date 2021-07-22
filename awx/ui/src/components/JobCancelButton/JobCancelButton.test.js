import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  ProjectUpdatesAPI,
  AdHocCommandsAPI,
  SystemJobsAPI,
  WorkflowJobsAPI,
  JobsAPI,
} from 'api';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import JobCancelButton from './JobCancelButton';

jest.mock('../../api');

describe('<JobCancelButton/>', () => {
  let wrapper;

  test('should render properly', () => {
    act(() => {
      wrapper = mountWithContexts(
        <JobCancelButton
          job={{ id: 1, type: 'project_update' }}
          errorTitle="Error"
          title="Title"
        />
      );
    });
    expect(wrapper.length).toBe(1);
    expect(wrapper.find('MinusCircleIcon').length).toBe(0);
  });
  test('should render icon button', () => {
    act(() => {
      wrapper = mountWithContexts(
        <JobCancelButton
          job={{ id: 1, type: 'project_update' }}
          errorTitle="Error"
          title="Title"
          showIconButton
        />
      );
    });
    expect(wrapper.find('MinusCircleIcon').length).toBe(1);
  });
  test('should call api', async () => {
    act(() => {
      wrapper = mountWithContexts(
        <JobCancelButton
          job={{ id: 1, type: 'project_update' }}
          errorTitle="Error"
          title="Title"
          showIconButton
        />
      );
    });
    await act(async () => wrapper.find('Button').prop('onClick')(true));
    wrapper.update();

    expect(wrapper.find('AlertModal').length).toBe(1);
    await act(() =>
      wrapper.find('Button#cancel-job-confirm-button').prop('onClick')()
    );
    expect(ProjectUpdatesAPI.cancel).toBeCalledWith(1);
  });
  test('should throw error', async () => {
    ProjectUpdatesAPI.cancel.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'post',
            url: '/api/v2/projectupdates',
          },
          data: 'An error occurred',
          status: 403,
        },
      })
    );
    act(() => {
      wrapper = mountWithContexts(
        <JobCancelButton
          job={{ id: 'a', type: 'project_update' }}
          errorTitle="Error"
          title="Title"
          showIconButton
        />
      );
    });
    await act(async () => wrapper.find('Button').prop('onClick')(true));
    wrapper.update();
    expect(wrapper.find('AlertModal').length).toBe(1);
    await act(() =>
      wrapper.find('Button#cancel-job-confirm-button').prop('onClick')()
    );
    wrapper.update();
    expect(wrapper.find('ErrorDetail').length).toBe(1);
    expect(wrapper.find('AlertModal[title="Title"]').length).toBe(0);
  });

  test('should cancel Ad Hoc Command job', async () => {
    act(() => {
      wrapper = mountWithContexts(
        <JobCancelButton
          job={{ id: 1, type: 'ad_hoc_command' }}
          errorTitle="Error"
          title="Title"
          showIconButton
        />
      );
    });
    await act(async () => wrapper.find('Button').prop('onClick')(true));
    wrapper.update();

    expect(wrapper.find('AlertModal').length).toBe(1);
    await act(() =>
      wrapper.find('Button#cancel-job-confirm-button').prop('onClick')()
    );
    expect(AdHocCommandsAPI.cancel).toBeCalledWith(1);
  });

  test('should cancel system job', async () => {
    act(() => {
      wrapper = mountWithContexts(
        <JobCancelButton
          job={{ id: 1, type: 'system_job' }}
          errorTitle="Error"
          title="Title"
          showIconButton
        />
      );
    });
    await act(async () => wrapper.find('Button').prop('onClick')(true));
    wrapper.update();

    expect(wrapper.find('AlertModal').length).toBe(1);
    await act(() =>
      wrapper.find('Button#cancel-job-confirm-button').prop('onClick')()
    );
    expect(SystemJobsAPI.cancel).toBeCalledWith(1);
  });

  test('should cancel workflow job', async () => {
    act(() => {
      wrapper = mountWithContexts(
        <JobCancelButton
          job={{ id: 1, type: 'workflow_job' }}
          errorTitle="Error"
          title="Title"
          showIconButton
        />
      );
    });
    await act(async () => wrapper.find('Button').prop('onClick')(true));
    wrapper.update();

    expect(wrapper.find('AlertModal').length).toBe(1);
    await act(() =>
      wrapper.find('Button#cancel-job-confirm-button').prop('onClick')()
    );
    expect(WorkflowJobsAPI.cancel).toBeCalledWith(1);
  });
  test('should cancel workflow job', async () => {
    act(() => {
      wrapper = mountWithContexts(
        <JobCancelButton
          job={{ id: 1, type: 'hakunah_matata' }}
          errorTitle="Error"
          title="Title"
          showIconButton
        />
      );
    });
    await act(async () => wrapper.find('Button').prop('onClick')(true));
    wrapper.update();

    expect(wrapper.find('AlertModal').length).toBe(1);
    await act(() =>
      wrapper.find('Button#cancel-job-confirm-button').prop('onClick')()
    );
    expect(JobsAPI.cancel).toBeCalledWith(1);
  });
});
