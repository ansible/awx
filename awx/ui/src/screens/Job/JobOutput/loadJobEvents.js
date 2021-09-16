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

// TODO merge into useJobEventsTree?
function normalizeEvents(job, events) {
  let countOffset = 0;
  if (!job?.result_traceback) {
    return {
      events,
      countOffset,
    };
  }

  const tracebackEvent = {
    counter: 1,
    created: null,
    event: null,
    type: null,
    stdout: job?.result_traceback,
    start_line: 0,
  };
  // TODO: set as event at index 0 and use exact counter as index in addEvents?
  const firstIndex = events.findIndex((jobEvent) => jobEvent.counter === 1);
  if (firstIndex && events[firstIndex]?.stdout) {
    const stdoutLines = events[firstIndex].stdout.split('\r\n');
    stdoutLines[0] = tracebackEvent.stdout;
    events[firstIndex].stdout = stdoutLines.join('\r\n');
  } else {
    countOffset += 1;
    events.unshift(tracebackEvent);
  }

  return {
    events,
    countOffset,
  };
}
