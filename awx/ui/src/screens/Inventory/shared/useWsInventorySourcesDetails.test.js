import React from 'react';
import { act } from 'react-dom/test-utils';
import WS from 'jest-websocket-mock';
import { InventorySourcesAPI } from 'api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import useWsInventorySourceDetails from './useWsInventorySourcesDetails';

jest.mock('../../../api/models/InventorySources');

function TestInner() {
  return <div />;
}
function Test({ inventorySource }) {
  const synced = useWsInventorySourceDetails(inventorySource);
  return <TestInner inventorySource={synced} />;
}

describe('useWsProject', () => {
  let wrapper;

  test('should return inventory source detail', async () => {
    const inventorySource = { id: 1 };
    await act(async () => {
      wrapper = await mountWithContexts(
        <Test inventorySource={inventorySource} />
      );
    });

    expect(wrapper.find('TestInner').prop('inventorySource')).toEqual(
      inventorySource
    );
    WS.clean();
  });

  test('should establish websocket connection', async () => {
    global.document.cookie = 'csrftoken=abc123';
    const mockServer = new WS('ws://localhost/websocket/');

    const inventorySource = { id: 1 };
    await act(async () => {
      wrapper = await mountWithContexts(
        <Test inventorySource={inventorySource} />
      );
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

  test('should update inventory source status', async () => {
    global.document.cookie = 'csrftoken=abc123';
    const mockServer = new WS('ws://localhost/websocket/');

    const inventorySource = {
      id: 1,
      summary_fields: {
        current_job: {
          id: 1,
          status: 'running',
          finished: null,
        },
      },
    };
    await act(async () => {
      wrapper = await mountWithContexts(
        <Test inventorySource={inventorySource} />
      );
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
      wrapper.find('TestInner').prop('inventorySource').summary_fields
        .current_job.status
    ).toEqual('running');

    await act(async () => {
      mockServer.send(
        JSON.stringify({
          group_name: 'jobs',
          inventory_id: 1,
          status: 'pending',
          type: 'inventory_source',
          unified_job_id: 2,
          unified_job_template_id: 1,
          inventory_source_id: 1,
        })
      );
    });
    wrapper.update();

    expect(
      wrapper.find('TestInner').prop('inventorySource').summary_fields
        .current_job
    ).toEqual({
      id: 1,
      status: 'running',
      finished: null,
    });

    expect(InventorySourcesAPI.readDetail).toHaveBeenCalledTimes(0);
    InventorySourcesAPI.readDetail.mockResolvedValue({
      data: {},
    });
    await act(async () => {
      mockServer.send(
        JSON.stringify({
          group_name: 'jobs',
          inventory_id: 1,
          status: 'successful',
          type: 'inventory_update',
          unified_job_id: 2,
          unified_job_template_id: 1,
          inventory_source_id: 1,
        })
      );
    });
    expect(InventorySourcesAPI.readDetail).toHaveBeenCalledTimes(1);

    jest.clearAllMocks();
    WS.clean();
  });
});
