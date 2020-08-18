import { useState, useEffect } from 'react';
import useWebsocket from '../../../util/useWebsocket';

export default function useWsInventorySources(initialSources) {
  const [sources, setSources] = useState(initialSources);
  const lastMessage = useWebsocket({
    jobs: ['status_changed'],
    control: ['limit_reached_1'],
  });

  useEffect(() => {
    setSources(initialSources);
  }, [initialSources]);

  useEffect(
    function parseWsMessage() {
      if (!lastMessage?.unified_job_id || !lastMessage?.inventory_source_id) {
        return;
      }

      const sourceId = lastMessage.inventory_source_id;
      const index = sources.findIndex(s => s.id === sourceId);
      if (index > -1) {
        setSources(updateSource(sources, index, lastMessage));
      }
    },
    [lastMessage] // eslint-disable-line react-hooks/exhaustive-deps
  );

  return sources;
}

function updateSource(sources, index, message) {
  const source = {
    ...sources[index],
    status: message.status,
    last_updated: message.finished,
    summary_fields: {
      ...sources[index].summary_fields,
      last_job: {
        id: message.unified_job_id,
        status: message.status,
        finished: message.finished,
      },
    },
  };
  return [...sources.slice(0, index), source, ...sources.slice(index + 1)];
}
