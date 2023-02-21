import { useState, useEffect } from 'react';
import useWebsocket from 'hooks/useWebsocket';
import { InventorySourcesAPI } from 'api';

export default function useWsInventorySourcesDetails(initialSource) {
  const [source, setSource] = useState(initialSource);
  const lastMessage = useWebsocket({
    jobs: ['status_changed'],
    control: ['limit_reached_1'],
  });

  useEffect(() => {
    setSource(initialSource);
  }, [initialSource]);

  useEffect(
    () => {
      if (
        !lastMessage?.unified_job_id ||
        !lastMessage?.inventory_source_id ||
        lastMessage.type !== 'inventory_update'
      ) {
        return;
      }

      if (
        ['successful', 'failed', 'error', 'cancelled'].includes(
          lastMessage.status
        )
      ) {
        fetchSource();
      }
      setSource(updateSource(source, lastMessage));
    },
    [lastMessage] // eslint-disable-line react-hooks/exhaustive-deps
  );

  async function fetchSource() {
    const { data } = await InventorySourcesAPI.readDetail(source.id);
    setSource(data);
  }

  return source;
}

function updateSource(source, message) {
  return {
    ...source,
    summary_fields: {
      ...source.summary_fields,
      current_job: {
        id: message.unified_job_id,
        status: message.status,
        finished: message.finished,
      },
    },
  };
}
