import { useState, useEffect } from 'react';
import useWebsocket from 'hooks/useWebsocket';
import { getJobModel } from 'util/jobs';

export default function useWsJob(initialJob) {
  const [job, setJob] = useState(initialJob);
  const [pendingMessages, setPendingMessages] = useState([]);
  const lastMessage = useWebsocket({
    jobs: ['status_changed'],
    control: ['limit_reached_1'],
  });

  useEffect(() => {
    setJob(initialJob);
  }, [initialJob]);

  const processMessage = (message) => {
    if (message.unified_job_id !== job.id) {
      return;
    }

    if (
      ['successful', 'failed', 'error', 'cancelled'].includes(message.status)
    ) {
      fetchJob();
    }
    setJob(updateJob(job, message));
  };

  async function fetchJob() {
    const { data } = await getJobModel(job.type).readDetail(job.id);
    setJob(data);
  }

  useEffect(
    () => {
      if (!lastMessage) {
        return;
      }
      if (job) {
        processMessage(lastMessage);
      } else if (lastMessage.unified_job_id) {
        setPendingMessages(pendingMessages.concat(lastMessage));
      }
    },
    [lastMessage] // eslint-disable-line react-hooks/exhaustive-deps
  );

  useEffect(() => {
    if (!job || !pendingMessages.length) {
      return;
    }
    pendingMessages.forEach((message) => {
      processMessage(message);
    });
    setPendingMessages([]);
  }, [job, pendingMessages]); // eslint-disable-line react-hooks/exhaustive-deps

  return job;
}

function updateJob(job, message) {
  return {
    ...job,
    finished: message.finished,
    status: message.status,
  };
}
