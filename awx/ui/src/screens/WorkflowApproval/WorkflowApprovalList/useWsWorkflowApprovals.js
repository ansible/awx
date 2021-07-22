import { useState, useEffect } from 'react';
import useWebsocket from 'hooks/useWebsocket';
import useThrottle from 'hooks/useThrottle';

export default function useWsWorkflowApprovals(
  initialWorkflowApprovals,
  fetchWorkflowApprovals
) {
  const [workflowApprovals, setWorkflowApprovals] = useState(
    initialWorkflowApprovals
  );
  const [reloadEntireList, setReloadEntireList] = useState(false);
  const throttledListRefresh = useThrottle(reloadEntireList, 1000);
  const lastMessage = useWebsocket({
    jobs: ['status_changed'],
    control: ['limit_reached_1'],
  });

  useEffect(() => {
    setWorkflowApprovals(initialWorkflowApprovals);
  }, [initialWorkflowApprovals]);

  useEffect(() => {
    (async () => {
      if (!throttledListRefresh) {
        return;
      }
      setReloadEntireList(false);
      fetchWorkflowApprovals();
    })();
  }, [throttledListRefresh, fetchWorkflowApprovals]);

  useEffect(
    () => {
      if (!(lastMessage?.type === 'workflow_approval')) {
        return;
      }

      const index = workflowApprovals.findIndex(
        (p) => p.id === lastMessage.unified_job_id
      );

      if (
        (index > -1 &&
          !['new', 'pending', 'waiting', 'running'].includes(
            lastMessage.status
          )) ||
        (index === -1 && lastMessage.status === 'pending')
      ) {
        setReloadEntireList(true);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps,
    [lastMessage]
  );

  return workflowApprovals;
}
