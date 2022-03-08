export default function webWorker() {
  return new Worker(new URL('./workers/simulationWorker.js', import.meta.url));
}
