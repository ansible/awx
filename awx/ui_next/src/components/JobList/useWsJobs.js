import { useState, useEffect, useRef } from 'react';

export default function useWsJobs(initialJobs, refetchJobs, filtersApplied) {
  const [jobs, setJobs] = useState(initialJobs);
  const [lastMessage, setLastMessage] = useState(null);
  useEffect(() => {
    setJobs(initialJobs);
  }, [initialJobs]);

  const ws = useRef(null);

  useEffect(() => {
    if (!lastMessage || !lastMessage.unified_job_id) {
      return;
    }
    if (filtersApplied) {
      if (['completed', 'failed', 'error'].includes(lastMessage.status)) {
        refetchJobs();
      }
      return;
    }

    const jobId = lastMessage.unified_job_id;
    const index = jobs.findIndex(j => j.id === jobId);
    if (index > -1) {
      setJobs(updateJob(jobs, index, lastMessage));
    } else {
      setJobs(addJobStub(jobs, lastMessage));
      refetchJobs();
    }
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
            schedules: ['changed'],
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
      ws.close();
    };

    return () => {
      ws.current.close();
    };
  }, []);

  return jobs;
}

function updateJob(jobs, index, message) {
  const job = {
    ...jobs[index],
    status: message.status,
    finished: message.finished,
  };
  return [...jobs.slice(0, index), job, ...jobs.slice(index + 1)];
}

function addJobStub(jobs, message) {
  const job = {
    id: message.unified_job_id,
    status: message.status,
    type: message.type,
    url: `/api/v2/jobs/${message.unified_job_id}`,
  };
  return [job, ...jobs];
}

//
// const initial = {
//   groups_current: [
//     'schedules-changed',
//     'control-limit_reached_1',
//     'jobs-status_changed',
//   ],
//   groups_left: [],
//   groups_joined: [
//     'schedules-changed',
//     'control-limit_reached_1',
//     'jobs-status_changed',
//   ],
// };
//
// const one = {
//   unified_job_id: 292,
//   status: 'pending',
//   type: 'job',
//   group_name: 'jobs',
//   unified_job_template_id: 26,
// };
// const two = {
//   unified_job_id: 292,
//   status: 'waiting',
//   instance_group_name: 'tower',
//   type: 'job',
//   group_name: 'jobs',
//   unified_job_template_id: 26,
// };
// const three = {
//   unified_job_id: 293,
//   status: 'running',
//   type: 'job',
//   group_name: 'jobs',
//   unified_job_template_id: 26,
// };
// const four = {
//   unified_job_id: 293,
//   status: 'successful',
//   finished: '2020-06-01T21:49:28.704114Z',
//   type: 'job',
//   group_name: 'jobs',
//   unified_job_template_id: 26,
// };
