import { getJobModel, isJobRunning } from 'util/jobs';

// TODO: merge back into JobOutput
// eslint-disable-next-line import/prefer-default-export
export async function fetchCount(job, eventPromise) {
  if (isJobRunning(job?.status)) {
    const {
      data: { results: lastEvents = [] },
    } = await getJobModel(job.type).readEvents(job.id, {
      order_by: '-counter',
      limit: 1,
    });
    return lastEvents.length >= 1 ? lastEvents[0].counter : 0;
  }

  const {
    data: { count: eventCount },
  } = await eventPromise;
  return eventCount;
}
