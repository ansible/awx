import { useState, useEffect, useRef } from 'react';

export default function useWsProjects(initialProjects) {
  const [projects, setProjects] = useState(initialProjects);
  const [lastMessage, setLastMessage] = useState(null);
  const ws = useRef(null);

  useEffect(() => {
    setProjects(initialProjects);
  }, [initialProjects]);

  useEffect(() => {
    if (!lastMessage?.unified_job_id || lastMessage.type !== 'project_update') {
      return;
    }
    const index = projects.findIndex(p => p.id === lastMessage.project_id);
    if (index === -1) {
      return;
    }

    const project = projects[index];
    const updatedProject = {
      ...project,
      summary_fields: {
        ...project.summary_fields,
        last_job: {
          id: lastMessage.unified_job_id,
          status: lastMessage.status,
          finished: lastMessage.finished,
        },
      },
    };
    setProjects([
      ...projects.slice(0, index),
      updatedProject,
      ...projects.slice(index + 1),
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

  return projects;
}
