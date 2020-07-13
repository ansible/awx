import React from 'react';
import { act } from 'react-dom/test-utils';
import WS from 'jest-websocket-mock';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import useWsInventories from './useWsInventories';

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
function Test({ inventories, fetch }) {
  const syncedJobs = useWsInventories(inventories, fetch);
  return <TestInner inventories={syncedJobs} />;
}

describe('useWsInventories hook', () => {
  let debug;
  let wrapper;
  beforeEach(() => {
    debug = global.console.debug; // eslint-disable-line prefer-destructuring
    global.console.debug = () => {};
  });

  afterEach(() => {
    global.console.debug = debug;
  });

  test('should return inventories list', () => {
    const inventories = [{ id: 1 }];
    wrapper = mountWithContexts(<Test inventories={inventories} />);

    expect(wrapper.find('TestInner').prop('inventories')).toEqual(inventories);
    WS.clean();
  });

  test('should establish websocket connection', async () => {
    global.document.cookie = 'csrftoken=abc123';
    const mockServer = new WS('wss://localhost/websocket/');

    const inventories = [{ id: 1 }];
    await act(async () => {
      wrapper = await mountWithContexts(<Test inventories={inventories} />);
    });

    await mockServer.connected;
    await expect(mockServer).toReceiveMessage(
      JSON.stringify({
        xrftoken: 'abc123',
        groups: {
          inventories: ['status_changed'],
          jobs: ['status_changed'],
          control: ['limit_reached_1'],
        },
      })
    );
    WS.clean();
  });

  test('should update inventory sync status', async () => {
    global.document.cookie = 'csrftoken=abc123';
    const mockServer = new WS('wss://localhost/websocket/');

    const inventories = [{ id: 1 }];
    await act(async () => {
      wrapper = await mountWithContexts(<Test inventories={inventories} />);
    });

    await mockServer.connected;
    await expect(mockServer).toReceiveMessage(
      JSON.stringify({
        xrftoken: 'abc123',
        groups: {
          inventories: ['status_changed'],
          jobs: ['status_changed'],
          control: ['limit_reached_1'],
        },
      })
    );
    act(() => {
      mockServer.send(
        JSON.stringify({
          inventory_id: 1,
          type: 'inventory_update',
          status: 'running',
        })
      );
    });
    wrapper.update();

    expect(
      wrapper.find('TestInner').prop('inventories')[0].isSourceSyncRunning
    ).toEqual(true);
    WS.clean();
  });

  test('should fetch fresh inventory after sync runs', async () => {
    global.document.cookie = 'csrftoken=abc123';
    const mockServer = new WS('wss://localhost/websocket/');
    const inventories = [{ id: 1 }];
    const fetch = jest.fn(() => []);
    await act(async () => {
      wrapper = await mountWithContexts(
        <Test inventories={inventories} fetch={fetch} />
      );
    });

    await mockServer.connected;
    await act(async () => {
      mockServer.send(
        JSON.stringify({
          inventory_id: 1,
          type: 'inventory_update',
          status: 'successful',
        })
      );
    });

    expect(fetch).toHaveBeenCalledWith([1]);
    WS.clean();
  });
});
