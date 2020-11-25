import { useState, useEffect } from 'react';
import useWebsocket from './useWebsocket';

export default function useWsTemplates(initialTemplates) {
  const [templates, setTemplates] = useState(initialTemplates);
  const lastMessage = useWebsocket({
    jobs: ['status_changed'],
    control: ['limit_reached_1'],
  });

  useEffect(() => {
    setTemplates(initialTemplates);
  }, [initialTemplates]);

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

  return templates;
}

function updateTemplate(template, message) {
  const recentJobs = [...(template.summary_fields.recent_jobs || [])];
  const job = {
    id: message.unified_job_id,
    status: message.status,
    finished: message.finished || null,
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
