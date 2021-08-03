import { useState, useEffect } from 'react';
import useWebsocket from 'hooks/useWebsocket';
import useThrottle from 'hooks/useThrottle';

export default function useWsPendingApprovalCount(
  initialCount,
  fetchApprovalsCount
) {
  const [pendingApprovalCount, setPendingApprovalCount] =
    useState(initialCount);
  const [reloadCount, setReloadCount] = useState(false);
  const throttledFetch = useThrottle(reloadCount, 1000);
  const lastMessage = useWebsocket({
    jobs: ['status_changed'],
    control: ['limit_reached_1'],
  });

  useEffect(() => {
    setPendingApprovalCount(initialCount);
  }, [initialCount]);

  useEffect(() => {
    (async () => {
      if (!throttledFetch) {
        return;
      }
      setReloadCount(false);
      fetchApprovalsCount();
    })();
  }, [throttledFetch, fetchApprovalsCount]);

  useEffect(() => {
    if (lastMessage?.type === 'workflow_approval') {
      setReloadCount(true);
    }
  }, [lastMessage]);

  return pendingApprovalCount;
}
