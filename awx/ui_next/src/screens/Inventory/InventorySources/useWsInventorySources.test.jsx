import React from 'react';
import { act } from 'react-dom/test-utils';
import WS from 'jest-websocket-mock';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import useWsInventorySources from './useWsInventorySources';

/*
  Jest mock timers don’t play well with jest-websocket-mock,
  so we'll stub out throttling to resolve immediately
*/
jest.mock('../../../util/useThrottle', () => ({
  __esModule: true,
  default: jest.fn(val => val),
}));

function TestInner() {
  return <div />;
}
function Test({ sources }) {
  const syncedSources = useWsInventorySources(sources);
  return <TestInner sources={syncedSources} />;
}

describe('useWsInventorySources hook', () => {
  let debug;
  let wrapper;
  beforeEach(() => {
    debug = global.console.debug; // eslint-disable-line prefer-destructuring
    global.console.debug = () => {};
  });

  afterEach(() => {
    global.console.debug = debug;
  });

  test('should return sources list', () => {
    const sources = [{ id: 1 }];
    wrapper = mountWithContexts(<Test sources={sources} />);

    expect(wrapper.find('TestInner').prop('sources')).toEqual(sources);
    WS.clean();
  });

  test('should establish websocket connection', async () => {
    global.document.cookie = 'csrftoken=abc123';
    const mockServer = new WS('wss://localhost/websocket/');

    const sources = [{ id: 1 }];
    await act(async () => {
      wrapper = await mountWithContexts(<Test sources={sources} />);
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

  test('should update last job status', async () => {
    global.document.cookie = 'csrftoken=abc123';
    const mockServer = new WS('wss://localhost/websocket/');

    const sources = [
      {
        id: 3,
        status: 'running',
        summary_fields: {
          last_job: {
            id: 5,
            status: 'running',
          },
        },
      },
    ];
    await act(async () => {
      wrapper = await mountWithContexts(<Test sources={sources} />);
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
    act(() => {
      mockServer.send(
        JSON.stringify({
          unified_job_id: 5,
          inventory_source_id: 3,
          type: 'job',
          status: 'successful',
          finished: 'the_time',
        })
      );
    });
    wrapper.update();

    const source = wrapper.find('TestInner').prop('sources')[0];
    expect(source).toEqual({
      id: 3,
      status: 'successful',
      last_updated: 'the_time',
      summary_fields: {
        last_job: {
          id: 5,
          status: 'successful',
          finished: 'the_time',
        },
      },
    });
    WS.clean();
  });
});
