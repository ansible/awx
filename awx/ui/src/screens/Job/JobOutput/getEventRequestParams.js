import getRowRangePageSize from './shared/jobOutputUtils';

export default function getEventRequestParams(
  job,
  remoteRowCount,
  requestRange
) {
  const [startIndex, stopIndex] = requestRange;
  const { page, pageSize, firstIndex } = getRowRangePageSize(
    startIndex,
    stopIndex
  );
  const loadRange = range(
    firstIndex + 1,
    Math.min(firstIndex + pageSize, remoteRowCount)
  );

  return [{ page, page_size: pageSize }, loadRange];
}

export function range(low, high) {
  const numbers = [];
  for (let n = low; n <= high; n++) {
    numbers.push(n);
  }
  return numbers;
}
