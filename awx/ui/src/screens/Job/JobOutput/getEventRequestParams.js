import { isJobRunning } from 'util/jobs';
import getRowRangePageSize from './shared/jobOutputUtils';

export default function getEventRequestParams(
  job,
  remoteRowCount,
  requestRange
) {
  const [startIndex, stopIndex] = requestRange;
  if (isJobRunning(job?.status)) {
    return [
      { counter__gte: startIndex, limit: stopIndex - startIndex + 1 },
      range(startIndex, Math.min(stopIndex, remoteRowCount)),
      startIndex,
    ];
  }
  const { page, pageSize, firstIndex } = getRowRangePageSize(
    startIndex,
    stopIndex
  );
  const loadRange = range(
    firstIndex,
    Math.min(firstIndex + pageSize, remoteRowCount)
  );

  return [{ page, page_size: pageSize }, loadRange, firstIndex];
}

function range(low, high) {
  const numbers = [];
  for (let n = low; n <= high; n++) {
    numbers.push(n);
  }
  return numbers;
}
