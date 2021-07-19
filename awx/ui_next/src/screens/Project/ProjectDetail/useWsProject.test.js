import React from 'react';
import { act } from 'react-dom/test-utils';
import WS from 'jest-websocket-mock';
import { ProjectsAPI } from 'api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import useWsProject from './useWsProject';

jest.mock('../../../api/models/Projects');

function TestInner() {
  return <div />;
}
function Test({ project }) {
  const synced = useWsProject(project);
  return <TestInner project={synced} />;
}

describe('useWsProject', () => {
  let debug;
  let wrapper;

  beforeEach(() => {
    debug = global.console.debug; // eslint-disable-line prefer-destructuring
    global.console.debug = () => {};
    ProjectsAPI.readDetail.mockResolvedValue({
      data: {
        id: 1,
        summary_fields: {
          last_job: {
            id: 19,
            name: 'Test Project',
            description: '',
            finished: '2021-06-01T18:43:53.332201Z',
            status: 'successful',
            failed: false,
          },
        },
      },
    });
  });

  afterEach(() => {
    global.console.debug = debug;
    jest.clearAllMocks();
  });

  test('should return project detail', async () => {
    const project = { id: 1 };
    await act(async () => {
      wrapper = await mountWithContexts(<Test project={project} />);
    });

    expect(wrapper.find('TestInner').prop('project')).toEqual(project);
    WS.clean();
  });

  test('should establish websocket connection', async () => {
    global.document.cookie = 'csrftoken=abc123';
    const mockServer = new WS('ws://localhost/websocket/');

    const project = { id: 1 };
    await act(async () => {
      wrapper = await mountWithContexts(<Test project={project} />);
    });

    await mockServer.connected;
    await expect(mockServer).toReceiveMessage(
      JSON.stringify({
        xrftoken: 'abc123',
        groups: {
          jobs: ['status_changed'],
          control: ['limit_reached_1'],
        },
      })
    );
    WS.clean();
  });

  test('should update project status', async () => {
    global.document.cookie = 'csrftoken=abc123';
    const mockServer = new WS('ws://localhost/websocket/');

    const project = {
      id: 1,
      summary_fields: {
        last_job: {
          id: 1,
          status: 'successful',
          finished: '2020-07-02T16:25:31.839071Z',
        },
      },
    };

    await act(async () => {
      wrapper = await mountWithContexts(<Test project={project} />);
    });

    await mockServer.connected;
    await expect(mockServer).toReceiveMessage(
      JSON.stringify({
        xrftoken: 'abc123',
        groups: {
          jobs: ['status_changed'],
          control: ['limit_reached_1'],
        },
      })
    );
    expect(
      wrapper.find('TestInner').prop('project').summary_fields.current_job
    ).toBeUndefined();
    expect(
      wrapper.find('TestInner').prop('project').summary_fields.last_job.status
    ).toEqual('successful');

    await act(async () => {
      mockServer.send(
        JSON.stringify({
          group_name: 'jobs',
          project_id: 1,
          status: 'running',
          type: 'project_update',
          unified_job_id: 2,
          unified_job_template_id: 1,
        })
      );
    });
    wrapper.update();

    expect(
      wrapper.find('TestInner').prop('project').summary_fields.current_job
    ).toEqual({
      id: 2,
      status: 'running',
      finished: undefined,
    });

    await act(async () => {
      mockServer.send(
        JSON.stringify({
          group_name: 'jobs',
          project_id: 1,
          status: 'successful',
          type: 'project_update',
          unified_job_id: 2,
          unified_job_template_id: 1,
          finished: '2020-07-02T16:28:31.839071Z',
        })
      );
    });

    wrapper.update();

    expect(ProjectsAPI.readDetail).toHaveBeenCalledTimes(1);

    expect(
      wrapper.find('TestInner').prop('project').summary_fields.last_job
    ).toEqual({
      id: 19,
      name: 'Test Project',
      description: '',
      finished: '2021-06-01T18:43:53.332201Z',
      status: 'successful',
      failed: false,
    });
    WS.clean();
  });
});
