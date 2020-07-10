import { useState, useEffect, useRef } from 'react';

export default function useWsTemplates(initialTemplates) {
  const [templates, setTemplates] = useState(initialTemplates);

  const [lastMessage, setLastMessage] = useState(null);
  const ws = useRef(null);

  useEffect(() => {
    setTemplates(initialTemplates);
  }, [initialTemplates]);

  // x = {
  //   unified_job_id: 548,
  //   status: 'pending',
  //   type: 'job',
  //   group_name: 'jobs',
  //   unified_job_template_id: 26,
  // };
  useEffect(
    function parseWsMessage() {
      if (!lastMessage?.unified_job_id) {
        return;
      }
      const index = templates.findIndex(
        t => t.id === lastMessage.unified_job_template_id
      );
      if (index === -1) {
        return;
      }

      const template = templates[index];
      const updated = [...templates];
      updated[index] = updateTemplate(template, lastMessage);
      setTemplates(updated);
    },
    [lastMessage] // eslint-disable-line react-hooks/exhaustive-deps
  );

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

  return templates;
}

function updateTemplate(template, message) {
  const recentJobs = [...(template.summary_fields.recent_jobs || [])];
  const job = {
    id: message.unified_job_id,
    status: message.status,
    finished: message.finished,
    type: message.type,
  };
  const index = recentJobs.findIndex(j => j.id === job.id);
  if (index > -1) {
    recentJobs[index] = {
      ...recentJobs[index],
      ...job,
    };
  } else {
    recentJobs.unshift(job);
  }

  return {
    ...template,
    summary_fields: {
      ...template.summary_fields,
      recent_jobs: recentJobs.slice(0, 10),
    },
  };
}
