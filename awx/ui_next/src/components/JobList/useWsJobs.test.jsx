import React from 'react';
import { act } from 'react-dom/test-utils';
import { mount } from 'enzyme';
import WS from 'jest-websocket-mock';
import useWsJobs from './useWsJobs';

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
function Test({ jobs, fetch }) {
  const syncedJobs = useWsJobs(jobs, fetch);
  return <TestInner jobs={syncedJobs} />;
}

describe('useWsJobs hook', () => {
  let debug;
  let wrapper;
  beforeEach(() => {
    debug = global.console.debug; // eslint-disable-line prefer-destructuring
    global.console.debug = () => {};
  });

  afterEach(() => {
    global.console.debug = debug;
  });

  test('should return jobs list', () => {
    const jobs = [{ id: 1 }];
    wrapper = mount(<Test jobs={jobs} />);

    expect(wrapper.find('TestInner').prop('jobs')).toEqual(jobs);
    WS.clean();
  });

  test('should establish websocket connection', async () => {
    global.document.cookie = 'csrftoken=abc123';
    const mockServer = new WS('wss://localhost/websocket/');

    const jobs = [{ id: 1 }];
    await act(async () => {
      wrapper = await mount(<Test jobs={jobs} />);
    });

    await mockServer.connected;
    await expect(mockServer).toReceiveMessage(
      JSON.stringify({
        xrftoken: 'abc123',
        groups: {
          jobs: ['status_changed'],
          schedules: ['changed'],
          control: ['limit_reached_1'],
        },
      })
    );
    WS.clean();
  });

  test('should update job status', async () => {
    global.document.cookie = 'csrftoken=abc123';
    const mockServer = new WS('wss://localhost/websocket/');

    const jobs = [{ id: 1, status: 'running' }];
    await act(async () => {
      wrapper = await mount(<Test jobs={jobs} />);
    });

    await mockServer.connected;
    await expect(mockServer).toReceiveMessage(
      JSON.stringify({
        xrftoken: 'abc123',
        groups: {
          jobs: ['status_changed'],
          schedules: ['changed'],
          control: ['limit_reached_1'],
        },
      })
    );
    expect(wrapper.find('TestInner').prop('jobs')[0].status).toEqual('running');
    act(() => {
      mockServer.send(
        JSON.stringify({
          unified_job_id: 1,
          status: 'successful',
        })
      );
    });
    wrapper.update();

    expect(wrapper.find('TestInner').prop('jobs')[0].status).toEqual(
      'successful'
    );
    WS.clean();
  });

  test('should fetch new job', async () => {
    global.document.cookie = 'csrftoken=abc123';
    const mockServer = new WS('wss://localhost/websocket/');
    const jobs = [{ id: 1 }];
    const fetch = jest.fn();
    await act(async () => {
      wrapper = await mount(<Test jobs={jobs} fetch={fetch} />);
    });

    await mockServer.connected;
    act(() => {
      mockServer.send(
        JSON.stringify({
          unified_job_id: 2,
          status: 'running',
        })
      );
    });

    expect(fetch).toHaveBeenCalledWith([2]);
    WS.clean();
  });
});
