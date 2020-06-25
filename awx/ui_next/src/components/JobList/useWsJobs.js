import { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import useThrottle from './useThrottle';
import { parseQueryString } from '../../util/qs';

export default function useWsJobs(initialJobs, fetchJobsById, qsConfig) {
  const location = useLocation();
  const [jobs, setJobs] = useState(initialJobs);
  const [lastMessage, setLastMessage] = useState(null);
  const [jobsToFetch, setJobsToFetch] = useState([]);
  const throttledJobsToFetch = useThrottle(jobsToFetch, 5000);

  useEffect(() => {
    setJobs(initialJobs);
  }, [initialJobs]);

  const enqueueJobId = id => {
    if (!jobsToFetch.includes(id)) {
      setJobsToFetch(ids => ids.concat(id));
    }
  };
  useEffect(() => {
    (async () => {
      if (!throttledJobsToFetch.length) {
        return;
      }
      setJobsToFetch([]);
      const newJobs = await fetchJobsById(throttledJobsToFetch);
      const deduplicated = newJobs.filter(
        job => !jobs.find(j => j.id === job.id)
      );
      if (deduplicated.length) {
        setJobs([...deduplicated, ...jobs]);
      }
    })();
  }, [throttledJobsToFetch, fetchJobsById]); // eslint-disable-line react-hooks/exhaustive-deps

  const ws = useRef(null);

  useEffect(() => {
    if (!lastMessage || !lastMessage.unified_job_id) {
      return;
    }
    const params = parseQueryString(qsConfig, location.search);
    const filtersApplied = Object.keys(params).length > 4;
    if (
      filtersApplied &&
      !['completed', 'failed', 'error'].includes(lastMessage.status)
    ) {
      return;
    }

    const jobId = lastMessage.unified_job_id;
    const index = jobs.findIndex(j => j.id === jobId);
    if (index > -1) {
      setJobs(sortJobs(updateJob(jobs, index, lastMessage), params.order_by));
    } else {
      enqueueJobId(lastMessage.unified_job_id);
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
      ws.current.close();
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

function sortJobs(jobs, orderBy) {
  if (orderBy !== '-finished') {
    return jobs;
  }

  return jobs.sort((a, b) => {
    if (!a.finished) {
      return -1;
    }
    if (!b.finished) {
      return 1;
    }

    const dateA = new Date(a.finished);
    const dateB = new Date(b.finished);
    if (dateA < dateB) {
      return 1;
    }
    if (dateA > dateB) {
      return -1;
    }
    return 0;
  });
}
