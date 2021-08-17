import { getJobModel, isJobRunning } from 'util/jobs';

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

export function normalizeEvents(job, events) {
  let countOffset = 0;
  if (job?.result_traceback) {
    const tracebackEvent = {
      counter: 1,
      created: null,
      event: null,
      type: null,
      stdout: job?.result_traceback,
      start_line: 0,
    };
    const firstIndex = events.findIndex((jobEvent) => jobEvent.counter === 1);
    if (firstIndex && events[firstIndex]?.stdout) {
      const stdoutLines = events[firstIndex].stdout.split('\r\n');
      stdoutLines[0] = tracebackEvent.stdout;
      events[firstIndex].stdout = stdoutLines.join('\r\n');
    } else {
      countOffset += 1;
      events.unshift(tracebackEvent);
    }
  }

  return {
    events,
    countOffset,
  };
}
