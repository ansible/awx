import React from 'react';
import { act } from 'react-dom/test-utils';
import WS from 'jest-websocket-mock';
import { mountWithContexts } from '../../testUtils/enzymeHelpers';
import useWsTemplates from './useWsTemplates';

/*
  Jest mock timers don’t play well with jest-websocket-mock,
  so we'll stub out throttling to resolve immediately
*/
jest.mock('./useThrottle', () => ({
  __esModule: true,
  default: jest.fn(val => val),
}));

function TestInner() {
  return <div />;
}
function Test({ templates }) {
  const syncedTemplates = useWsTemplates(templates);
  return <TestInner templates={syncedTemplates} />;
}

describe('useWsTemplates hook', () => {
  let debug;
  let wrapper;
  beforeEach(() => {
    debug = global.console.debug; // eslint-disable-line prefer-destructuring
    global.console.debug = () => {};
  });

  afterEach(() => {
    global.console.debug = debug;
  });

  test('should return templates list', () => {
    const templates = [{ id: 1 }];
    wrapper = mountWithContexts(<Test templates={templates} />);

    expect(wrapper.find('TestInner').prop('templates')).toEqual(templates);
    WS.clean();
  });

  test('should establish websocket connection', async () => {
    global.document.cookie = 'csrftoken=abc123';
    const mockServer = new WS('wss://localhost/websocket/');

    const templates = [{ id: 1 }];
    await act(async () => {
      wrapper = await mountWithContexts(<Test templates={templates} />);
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

  test('should update recent job status', async () => {
    global.document.cookie = 'csrftoken=abc123';
    const mockServer = new WS('wss://localhost/websocket/');

    const templates = [
      {
        id: 1,
        summary_fields: {
          recent_jobs: [
            {
              id: 10,
              type: 'job',
              status: 'running',
            },
            {
              id: 11,
              type: 'job',
              status: 'successful',
            },
          ],
        },
      },
    ];
    await act(async () => {
      wrapper = await mountWithContexts(<Test templates={templates} />);
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
      wrapper.find('TestInner').prop('templates')[0].summary_fields
        .recent_jobs[0].status
    ).toEqual('running');
    act(() => {
      mockServer.send(
        JSON.stringify({
          unified_job_template_id: 1,
          unified_job_id: 10,
          type: 'job',
          status: 'successful',
        })
      );
    });
    wrapper.update();

    expect(
      wrapper.find('TestInner').prop('templates')[0].summary_fields
        .recent_jobs[0].status
    ).toEqual('successful');
    WS.clean();
  });

  test('should add new job status', async () => {
    global.document.cookie = 'csrftoken=abc123';
    const mockServer = new WS('wss://localhost/websocket/');

    const templates = [
      {
        id: 1,
        summary_fields: {
          recent_jobs: [
            {
              id: 10,
              type: 'job',
              status: 'running',
            },
            {
              id: 11,
              type: 'job',
              status: 'successful',
            },
          ],
        },
      },
    ];
    await act(async () => {
      wrapper = await mountWithContexts(<Test templates={templates} />);
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
      wrapper.find('TestInner').prop('templates')[0].summary_fields
        .recent_jobs[0].status
    ).toEqual('running');
    act(() => {
      mockServer.send(
        JSON.stringify({
          unified_job_template_id: 1,
          unified_job_id: 13,
          type: 'job',
          status: 'running',
        })
      );
    });
    wrapper.update();

    expect(
      wrapper.find('TestInner').prop('templates')[0].summary_fields.recent_jobs
    ).toHaveLength(3);
    expect(
      wrapper.find('TestInner').prop('templates')[0].summary_fields
        .recent_jobs[0]
    ).toEqual({
      id: 13,
      status: 'running',
      finished: null,
      type: 'job',
    });
    WS.clean();
  });
});
