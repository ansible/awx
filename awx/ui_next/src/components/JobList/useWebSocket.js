import { useState, useEffect, useCallback, useRef } from 'react';
import useRequest from '../../util/useRequest';
import { UnifiedJobsAPI } from '../../api';

// rename: useWsJobs ?
export default function useWebSocket(params) {
  const [jobs, setJobs] = useState([]);
  const {
    result: { results, count },
    error: contentError,
    isLoading,
    request: fetchJobs,
  } = useRequest(
    useCallback(async () => {
      console.log('fetching...');
      const { data } = await UnifiedJobsAPI.read({ ...params });
      return data;
    }, [params]),
    { results: [], count: 0 }
  );
  useEffect(() => {
    fetchJobs();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    setJobs(results);
  }, [results]);
  const ws = useRef(null);

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
      const data = JSON.parse(e.data);
      // console.log(JSON.parse(e.data));
      const jobId = data.unified_job_id;
      if (!jobId) {
        return;
      }

      // TODO: Pull this function up... jobs is being closed over
      const index = jobs.findIndex(j => j.id === jobId);
      console.log('index', index);
      console.log(jobId, typeof jobId, jobs);
      if (index > -1) {
        const job = {
          ...jobs[index],
          status: data.status,
          finished: data.finished,
        };
        console.log('updated job:', job);
        const newJobs = [
          ...jobs.slice(0, index),
          job,
          ...jobs.slice(index + 1),
        ];
        console.log('updating jobs: ', newJobs);
        setJobs(newJobs);
      }
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

  return {
    jobs,
    count,
    contentError,
    isLoading,
    fetchJobs,
  };
}

const initial = {
  groups_current: [
    'schedules-changed',
    'control-limit_reached_1',
    'jobs-status_changed',
  ],
  groups_left: [],
  groups_joined: [
    'schedules-changed',
    'control-limit_reached_1',
    'jobs-status_changed',
  ],
};

const one = {
  unified_job_id: 292,
  status: 'pending',
  type: 'job',
  group_name: 'jobs',
  unified_job_template_id: 26,
};
const two = {
  unified_job_id: 292,
  status: 'waiting',
  instance_group_name: 'tower',
  type: 'job',
  group_name: 'jobs',
  unified_job_template_id: 26,
};
const three = {
  unified_job_id: 293,
  status: 'running',
  type: 'job',
  group_name: 'jobs',
  unified_job_template_id: 26,
};
const four = {
  unified_job_id: 293,
  status: 'successful',
  finished: '2020-06-01T21:49:28.704114Z',
  type: 'job',
  group_name: 'jobs',
  unified_job_template_id: 26,
};
