import getRowRangePageSize from './jobOutputUtils';

describe('getRowRangePageSize', () => {
  test('handles range of 1', () => {
    expect(getRowRangePageSize(1, 1)).toEqual({
      page: 1,
      pageSize: 1,
      firstIndex: 0,
    });
  });

  test('handles range of 1 at a higher number', () => {
    expect(getRowRangePageSize(72, 72)).toEqual({
      page: 72,
      pageSize: 1,
      firstIndex: 71,
    });
  });

  test('handles range larger than 50 rows', () => {
    expect(getRowRangePageSize(55, 125)).toEqual({
      page: 2,
      pageSize: 50,
      firstIndex: 50,
    });
  });

  test('handles small range', () => {
    expect(getRowRangePageSize(47, 53)).toEqual({
      page: 6,
      pageSize: 9,
      firstIndex: 45,
    });
  });

  test('handles perfect range', () => {
    expect(getRowRangePageSize(5, 9)).toEqual({
      page: 2,
      pageSize: 5,
      firstIndex: 5,
    });
  });

  test('handles range with 0 startIndex', () => {
    expect(getRowRangePageSize(0, 50)).toEqual({
      page: 1,
      pageSize: 50,
      firstIndex: 0,
    });
  });
});
