import { useState, useEffect } from 'react';
import useWebsocket from '../../../util/useWebsocket';

export default function useWsProjects(initialProject) {
  const [project, setProject] = useState(initialProject);
  const lastMessage = useWebsocket({
    jobs: ['status_changed'],
    control: ['limit_reached_1'],
  });

  useEffect(() => {
    setProject(initialProject);
  }, [initialProject]);

  useEffect(
    () => {
      if (
        !project ||
        !lastMessage?.unified_job_id ||
        lastMessage.type !== 'project_update'
      ) {
        return;
      }

      const updatedProject = {
        ...project,
        summary_fields: {
          ...project.summary_fields,
          current_job: {
            id: lastMessage.unified_job_id,
            status: lastMessage.status,
            finished: lastMessage.finished,
          },
        },
      };
      setProject(updatedProject);
    },
    [lastMessage] // eslint-disable-line react-hooks/exhaustive-deps
  );

  return project;
}
