export default function webWorker() {
  return new Worker(
    new URL(
      'screens/TopologyView/utils/workers/simulationWorker.js',
      import.meta.url
    )
  );
}
