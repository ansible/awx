import { useState, useEffect } from 'react';
import useWebsocket from 'hooks/useWebsocket';

export default function useWsInventorySourcesDetails(initialSources) {
  const [sources, setSources] = useState(initialSources);
  const lastMessage = useWebsocket({
    jobs: ['status_changed'],
    control: ['limit_reached_1'],
  });

  useEffect(() => {
    setSources(initialSources);
  }, [initialSources]);

  useEffect(
    () => {
      if (
        !lastMessage?.unified_job_id ||
        !lastMessage?.inventory_source_id ||
        lastMessage.type !== 'inventory_update'
      ) {
        return;
      }
      const updateSource = {
        ...sources,
        summary_fields: {
          ...sources.summary_fields,
          current_job: {
            id: lastMessage.unified_job_id,
            status: lastMessage.status,
            finished: lastMessage.finished,
          },
        },
      };

      setSources(updateSource);
    },
    [lastMessage] // eslint-disable-line react-hooks/exhaustive-deps
  );

  return sources;
}
