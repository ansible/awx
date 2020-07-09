import { useState, useEffect } from 'react';
import useWebsocket from '../../../util/useWebsocket';

export default function useWsProjects(initialProjects) {
  const [projects, setProjects] = useState(initialProjects);
  const lastMessage = useWebsocket({
    jobs: ['status_changed'],
    control: ['limit_reached_1'],
  });

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

  return projects;
}
