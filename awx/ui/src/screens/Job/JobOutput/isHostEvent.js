export default function isHostEvent(jobEvent) {
  const { event, event_data, host, type } = jobEvent;
  let isHost;
  if (typeof host === 'number' || (event_data && event_data.res)) {
    isHost = true;
  } else if (
    type === 'project_update_event' &&
    event !== 'runner_on_skipped' &&
    event_data.host
  ) {
    isHost = true;
  } else {
    isHost = false;
  }
  return isHost;
}
