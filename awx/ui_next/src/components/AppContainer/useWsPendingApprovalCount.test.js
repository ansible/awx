import React from 'react';
import { act } from 'react-dom/test-utils';
import WS from 'jest-websocket-mock';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import useWsPendingApprovalCount from './useWsPendingApprovalCount';

function TestInner() {
  return <div />;
}
function Test({ initialCount, fetchApprovalsCount }) {
  const updatedWorkflowApprovals = useWsPendingApprovalCount(
    initialCount,
    fetchApprovalsCount
  );
  return <TestInner initialCount={updatedWorkflowApprovals} />;
}

describe('useWsPendingApprovalCount hook', () => {
  let debug;
  let wrapper;
  beforeEach(() => {
    /*
      Jest mock timers don’t play well with jest-websocket-mock,
      so we'll stub out throttling to resolve immediately
    */
    jest.mock('../../hooks/useThrottle', () => ({
      __esModule: true,
      default: jest.fn((val) => val),
    }));
    debug = global.console.debug; // eslint-disable-line prefer-destructuring
    global.console.debug = () => {};
  });

  afterEach(() => {
    global.console.debug = debug;
    WS.clean();
  });

  test('should return workflow approval pending count', () => {
    wrapper = mountWithContexts(
      <Test initialCount={2} fetchApprovalsCount={() => {}} />
    );

    expect(wrapper.find('TestInner').prop('initialCount')).toEqual(2);
  });

  test('should establish websocket connection', async () => {
    global.document.cookie = 'csrftoken=abc123';
    const mockServer = new WS('ws://localhost/websocket/');

    await act(async () => {
      wrapper = mountWithContexts(
        <Test initialCount={2} fetchApprovalsCount={() => {}} />
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
  });

  test('should refetch count after approval status changes', async () => {
    global.document.cookie = 'csrftoken=abc123';
    const mockServer = new WS('ws://localhost/websocket/');
    const fetchApprovalsCount = jest.fn(() => []);
    await act(async () => {
      wrapper = await mountWithContexts(
        <Test initialCount={2} fetchApprovalsCount={fetchApprovalsCount} />
      );
    });

    await mockServer.connected;
    await act(async () => {
      mockServer.send(
        JSON.stringify({
          unified_job_id: 2,
          type: 'workflow_approval',
          status: 'pending',
        })
      );
    });

    expect(fetchApprovalsCount).toHaveBeenCalledTimes(1);
  });

  test('should not refetch when message is not workflow approval', async () => {
    global.document.cookie = 'csrftoken=abc123';
    const mockServer = new WS('ws://localhost/websocket/');
    const fetchApprovalsCount = jest.fn(() => []);
    await act(async () => {
      wrapper = await mountWithContexts(
        <Test initialCount={2} fetchApprovalsCount={fetchApprovalsCount} />
      );
    });

    await mockServer.connected;
    await act(async () => {
      mockServer.send(
        JSON.stringify({
          unified_job_id: 1,
          type: 'job',
          status: 'successful',
        })
      );
    });

    expect(fetchApprovalsCount).toHaveBeenCalledTimes(0);
  });
});
