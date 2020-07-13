import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import useWebsocket from '../../util/useWebsocket';
import useThrottle from '../../util/useThrottle';
import { parseQueryString } from '../../util/qs';
import sortJobs from './sortJobs';

export default function useWsJobs(initialJobs, fetchJobsById, qsConfig) {
  const location = useLocation();
  const [jobs, setJobs] = useState(initialJobs);
  const [jobsToFetch, setJobsToFetch] = useState([]);
  const throttledJobsToFetch = useThrottle(jobsToFetch, 5000);
  const lastMessage = useWebsocket({
    jobs: ['status_changed'],
    schedules: ['changed'],
    control: ['limit_reached_1'],
  });

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
        const params = parseQueryString(qsConfig, location.search);
        setJobs(sortJobs([...deduplicated, ...jobs], params));
      }
    })();
  }, [throttledJobsToFetch, fetchJobsById]); // eslint-disable-line react-hooks/exhaustive-deps

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
      setJobs(sortJobs(updateJob(jobs, index, lastMessage), params));
    } else {
      enqueueJobId(lastMessage.unified_job_id);
    }
  }, [lastMessage]); // eslint-disable-line react-hooks/exhaustive-deps

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
