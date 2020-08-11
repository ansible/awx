import React from 'react';
import { act } from 'react-dom/test-utils';
import WS from 'jest-websocket-mock';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import useWsProjects from './useWsProjects';

function TestInner() {
  return <div />;
}
function Test({ projects }) {
  const synced = useWsProjects(projects);
  return <TestInner projects={synced} />;
}

describe('useWsProjects', () => {
  let debug;
  let wrapper;
  beforeEach(() => {
    debug = global.console.debug; // eslint-disable-line prefer-destructuring
    global.console.debug = () => {};
  });

  afterEach(() => {
    global.console.debug = debug;
  });

  test('should return projects list', async () => {
    const projects = [{ id: 1 }];
    await act(async () => {
      wrapper = await mountWithContexts(<Test projects={projects} />);
    });

    expect(wrapper.find('TestInner').prop('projects')).toEqual(projects);
    WS.clean();
  });

  test('should establish websocket connection', async () => {
    global.document.cookie = 'csrftoken=abc123';
    const mockServer = new WS('wss://localhost/websocket/');

    const projects = [{ id: 1 }];
    await act(async () => {
      wrapper = await mountWithContexts(<Test projects={projects} />);
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
    const mockServer = new WS('wss://localhost/websocket/');

    const projects = [
      {
        id: 1,
        summary_fields: {
          last_job: {
            id: 1,
            status: 'running',
            finished: null,
          },
        },
      },
    ];
    await act(async () => {
      wrapper = await mountWithContexts(<Test projects={projects} />);
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
      wrapper.find('TestInner').prop('projects')[0].summary_fields.last_job
        .status
    ).toEqual('running');
    await act(async () => {
      mockServer.send(
        JSON.stringify({
          project_id: 1,
          unified_job_id: 12,
          type: 'project_update',
          status: 'successful',
          finished: '2020-07-02T16:28:31.839071Z',
        })
      );
    });
    wrapper.update();

    expect(
      wrapper.find('TestInner').prop('projects')[0].summary_fields.last_job
    ).toEqual({
      id: 12,
      status: 'successful',
      finished: '2020-07-02T16:28:31.839071Z',
    });
    WS.clean();
  });
});
