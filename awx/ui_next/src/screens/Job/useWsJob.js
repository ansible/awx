import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import useWebsocket from '../../util/useWebsocket';
import { JobsAPI } from '../../api';

export default function useWsJob(initialJob) {
  const { type } = useParams();
  const [job, setJob] = useState(initialJob);
  const lastMessage = useWebsocket({
    jobs: ['status_changed'],
    control: ['limit_reached_1'],
  });

  useEffect(() => {
    setJob(initialJob);
  }, [initialJob]);

  useEffect(
    function parseWsMessage() {
      async function fetchJob() {
        const { data } = await JobsAPI.readDetail(job.id, type);
        setJob(data);
      }

      if (!job || lastMessage?.unified_job_id !== job.id) {
        return;
      }

      if (
        ['successful', 'failed', 'error', 'cancelled'].includes(
          lastMessage.status
        )
      ) {
        fetchJob();
      } else {
        setJob(updateJob(job, lastMessage));
      }
    },
    [lastMessage] // eslint-disable-line react-hooks/exhaustive-deps
  );

  return job;
}

function updateJob(job, message) {
  return {
    ...job,
    finished: message.finished,
    status: message.status,
  };
}
