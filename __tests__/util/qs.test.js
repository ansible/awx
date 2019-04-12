import { encodeQueryString, parseQueryString } from '../../src/util/qs';

describe('qs (qs.js)', () => {
  test('encodeQueryString returns the expected queryString', () => {
    [
      [null, ''],
      [{}, ''],
      [{ order_by: 'name', page: 1, page_size: 5 }, 'order_by=name&page=1&page_size=5'],
      [{ '-order_by': 'name', page: '1', page_size: 5 }, '-order_by=name&page=1&page_size=5'],
    ]
      .forEach(([params, expectedQueryString]) => {
        const actualQueryString = encodeQueryString(params);

        expect(actualQueryString).toEqual(expectedQueryString);
      });
  });

  test('parseQueryString returns the expected queryParams', () => {
    [
      ['order_by=name&page=1&page_size=5', ['page', 'page_size'], { order_by: 'name', page: 1, page_size: 5 }],
      ['order_by=name&page=1&page_size=5', ['page_size'], { order_by: 'name', page: '1', page_size: 5 }],
    ]
      .forEach(([queryString, integerFields, expectedQueryParams]) => {
        const actualQueryParams = parseQueryString(queryString, integerFields);

        expect(actualQueryParams).toEqual(expectedQueryParams);
      });
  });
});
