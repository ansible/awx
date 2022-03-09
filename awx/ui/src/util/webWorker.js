export default function webWorker() {
  return new Worker(new URL('./simulationWorker.js', import.meta.url));
}
