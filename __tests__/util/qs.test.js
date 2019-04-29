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

  test('encodeQueryString omits null values', () => {
    const vals = {
      order_by: 'name',
      page: null,
    };
    expect(encodeQueryString(vals)).toEqual('order_by=name');
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

  test('parseQueryString should strip leading "?"', () => {
    expect(parseQueryString('?foo=bar&order_by=win')).toEqual({
      foo: 'bar',
      order_by: 'win',
    });

    expect(parseQueryString('foo=bar&order_by=?win')).toEqual({
      foo: 'bar',
      order_by: '?win',
    });
  });
});
