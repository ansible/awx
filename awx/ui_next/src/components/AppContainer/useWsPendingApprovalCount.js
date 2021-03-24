import { useState, useEffect } from 'react';
import useWebsocket from '../../util/useWebsocket';
import useThrottle from '../../util/useThrottle';

export default function useWsPendingApprovalCount(
  initialCount,
  fetchApprovalsCount
) {
  const [pendingApprovalCount, setPendingApprovalCount] = useState(
    initialCount
  );
  const [reloadCount, setReloadCount] = useState(false);
  const throttledFetch = useThrottle(reloadCount, 1000);
  const lastMessage = useWebsocket({
    jobs: ['status_changed'],
    control: ['limit_reached_1'],
  });

  useEffect(() => {
    setPendingApprovalCount(initialCount);
  }, [initialCount]);

  useEffect(
    function reloadTheCount() {
      (async () => {
        if (!throttledFetch) {
          return;
        }
        setReloadCount(false);
        fetchApprovalsCount();
      })();
    },
    [throttledFetch, fetchApprovalsCount]
  );

  useEffect(
    function processWsMessage() {
      if (lastMessage?.type === 'workflow_approval') {
        setReloadCount(true);
      }
    },
    [lastMessage]
  );

  return pendingApprovalCount;
}
