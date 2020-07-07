import { useState, useEffect, useRef } from 'react';

export default function useWsProjects(initialInventories) {
  const [inventories, setInventories] = useState(initialInventories);
  const [lastMessage, setLastMessage] = useState(null);
  const ws = useRef(null);

  useEffect(() => {
    setInventories(initialInventories);
  }, [initialInventories]);

  // const messageExample = {
  //   unified_job_id: 533,
  //   status: 'pending',
  //   type: 'inventory_update',
  //   inventory_source_id: 53,
  //   inventory_id: 5,
  //   group_name: 'jobs',
  //   unified_job_template_id: 53,
  // };
  useEffect(() => {
    if (!lastMessage?.unified_job_id || lastMessage.type !== 'project_update') {
      return;
    }
    const index = inventories.findIndex(p => p.id === lastMessage.project_id);
    if (index === -1) {
      return;
    }

    const inventory = inventories[index];
    const updatedProject = {
      ...inventory,
      summary_fields: {
        ...inventory.summary_fields,
        // last_job: {
        //   id: lastMessage.unified_job_id,
        //   status: lastMessage.status,
        //   finished: lastMessage.finished,
        // },
      },
    };
    setInventories([
      ...inventories.slice(0, index),
      updatedProject,
      ...inventories.slice(index + 1),
    ]);
  }, [lastMessage]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    ws.current = new WebSocket(`wss://${window.location.host}/websocket/`);

    const connect = () => {
      const xrftoken = `; ${document.cookie}`
        .split('; csrftoken=')
        .pop()
        .split(';')
        .shift();
      ws.current.send(
        JSON.stringify({
          xrftoken,
          groups: {
            inventories: ['status_changed'],
            jobs: ['status_changed'],
            control: ['limit_reached_1'],
          },
        })
      );
    };
    ws.current.onopen = connect;

    ws.current.onmessage = e => {
      setLastMessage(JSON.parse(e.data));
    };

    ws.current.onclose = e => {
      // eslint-disable-next-line no-console
      console.debug('Socket closed. Reconnecting...', e);
      setTimeout(() => {
        connect();
      }, 1000);
    };

    ws.current.onerror = err => {
      // eslint-disable-next-line no-console
      console.debug('Socket error: ', err, 'Disconnecting...');
      ws.current.close();
    };

    return () => {
      ws.current.close();
    };
  }, []);

  return inventories;
}
