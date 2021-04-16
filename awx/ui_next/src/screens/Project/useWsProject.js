import { useState, useEffect } from 'react';
import useWebsocket from '../../util/useWebsocket';

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

      const last_status = project.summary_fields.last_job.status;

      // In case if users spam the sync button, we will need to ensure
      // the fluent UI on most recent sync tooltip and last job status.
      // Thus, we will not update our last job status to `Pending` if
      // there is current running job.
      //
      // For instance, we clicked sync for particular project for twice.
      // For first sync, our last job status should immediately change
      // to `Pending`, then `Waiting`, then `Running`, then result
      // (which are `successful`, `failed`, `error`, `cancelled`.
      // For second sync, if the status response is `pending` and we have
      // running and waiting jobs, we should not update our UI to `Pending`,
      // otherwise our most recent sync tooltip UI will lose our current running
      // job and we cannot navigate to the job link through the link provided
      // by most recent sync tooltip.
      //
      // More ideally, we should prevent any spamming on sync button using
      // backend logic to reduce overload on server and we can have a
      // less complex frontend implementation for fluent UI
      if (
        lastMessage.status === 'pending' &&
        !['successful', 'failed', 'error', 'cancelled'].includes(last_status)
      ) {
        return;
      }
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
      setProject(updatedProject);
    },
    [lastMessage] // eslint-disable-line react-hooks/exhaustive-deps
  );

  return project;
}
