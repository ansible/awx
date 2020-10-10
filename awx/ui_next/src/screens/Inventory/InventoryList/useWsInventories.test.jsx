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
function Test({
  inventories,
  fetchInventories,
  fetchInventoriesById,
  qsConfig,
}) {
  const syncedInventories = useWsInventories(
    inventories,
    fetchInventories,
    fetchInventoriesById,
    qsConfig
  );
  return <TestInner inventories={syncedInventories} />;
}

const QS_CONFIG = {
  defaultParams: {},
};

describe('useWsInventories hook', () => {
  let debug;
  let wrapper;
  beforeEach(() => {
    debug = global.console.debug; // eslint-disable-line prefer-destructuring
    global.console.debug = () => {};
  });

  afterEach(() => {
    global.console.debug = debug;
    WS.clean();
  });

  test('should return inventories list', () => {
    const inventories = [{ id: 1 }];
    wrapper = mountWithContexts(
      <Test inventories={inventories} qsConfig={QS_CONFIG} />
    );

    expect(wrapper.find('TestInner').prop('inventories')).toEqual(inventories);
  });

  test('should establish websocket connection', async () => {
    global.document.cookie = 'csrftoken=abc123';
    const mockServer = new WS('wss://localhost/websocket/');

    const inventories = [{ id: 1 }];
    await act(async () => {
      wrapper = await mountWithContexts(
        <Test inventories={inventories} qsConfig={QS_CONFIG} />
      );
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
  });

  test('should update inventory sync status', async () => {
    global.document.cookie = 'csrftoken=abc123';
    const mockServer = new WS('wss://localhost/websocket/');

    const inventories = [{ id: 1 }];
    await act(async () => {
      wrapper = await mountWithContexts(
        <Test inventories={inventories} qsConfig={QS_CONFIG} />
      );
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
  });

  test('should fetch fresh inventory after sync runs', async () => {
    global.document.cookie = 'csrftoken=abc123';
    const mockServer = new WS('wss://localhost/websocket/');
    const inventories = [{ id: 1 }];
    const fetchInventories = jest.fn(() => []);
    const fetchInventoriesById = jest.fn(() => []);
    await act(async () => {
      wrapper = await mountWithContexts(
        <Test
          inventories={inventories}
          fetchInventories={fetchInventories}
          fetchInventoriesById={fetchInventoriesById}
          qsConfig={QS_CONFIG}
        />
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

    expect(fetchInventoriesById).toHaveBeenCalledWith([1]);
  });

  test('should update inventory pending_deletion', async () => {
    global.document.cookie = 'csrftoken=abc123';
    const mockServer = new WS('wss://localhost/websocket/');

    const inventories = [{ id: 1, pending_deletion: false }];
    await act(async () => {
      wrapper = await mountWithContexts(
        <Test inventories={inventories} qsConfig={QS_CONFIG} />
      );
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
          group_name: 'inventories',
          status: 'pending_deletion',
        })
      );
    });
    wrapper.update();

    expect(
      wrapper.find('TestInner').prop('inventories')[0].pending_deletion
    ).toEqual(true);
  });

  test('should refetch inventories after an inventory is deleted', async () => {
    global.document.cookie = 'csrftoken=abc123';
    const mockServer = new WS('wss://localhost/websocket/');
    const inventories = [{ id: 1 }, { id: 2 }];
    const fetchInventories = jest.fn(() => []);
    const fetchInventoriesById = jest.fn(() => []);
    await act(async () => {
      wrapper = await mountWithContexts(
        <Test
          inventories={inventories}
          fetchInventories={fetchInventories}
          fetchInventoriesById={fetchInventoriesById}
          qsConfig={QS_CONFIG}
        />
      );
    });

    await mockServer.connected;
    await act(async () => {
      mockServer.send(
        JSON.stringify({
          inventory_id: 1,
          group_name: 'inventories',
          status: 'deleted',
        })
      );
    });

    expect(fetchInventories).toHaveBeenCalled();
  });
});
