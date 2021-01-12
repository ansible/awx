export default function isJobRunning(status) {
  return ['new', 'pending', 'waiting', 'running'].includes(status);
}
