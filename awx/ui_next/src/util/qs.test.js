import {
  encodeQueryString,
  parseQueryString,
  getQSConfig,
  parseNamespacedQueryString,
  encodeNamespacedQueryString,
  updateNamespacedQueryString,
} from './qs';

describe('qs (qs.js)', () => {
  test('encodeQueryString returns the expected queryString', () => {
    [
      [null, ''],
      [{}, ''],
      [
        { order_by: 'name', page: 1, page_size: 5 },
        'order_by=name&page=1&page_size=5',
      ],
      [
        { '-order_by': 'name', page: '1', page_size: 5 },
        '-order_by=name&page=1&page_size=5',
      ],
    ].forEach(([params, expectedQueryString]) => {
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

  describe('parseQueryString', () => {
    test('parseQueryString returns the expected queryParams', () => {
      [
        [
          'order_by=name&page=1&page_size=5',
          ['page', 'page_size'],
          { order_by: 'name', page: 1, page_size: 5 },
        ],
        [
          'order_by=name&page=1&page_size=5',
          ['page_size'],
          { order_by: 'name', page: '1', page_size: 5 },
        ],
      ].forEach(([queryString, integerFields, expectedQueryParams]) => {
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

    test('should return empty object if no values', () => {
      expect(parseQueryString('')).toEqual({});
    });
  });

  test('should get default QS config object', () => {
    expect(getQSConfig('organization')).toEqual({
      namespace: 'organization',
      defaultParams: { page: 1, page_size: 5, order_by: 'name' },
      integerFields: ['page', 'page_size'],
    });
  });

  test('should throw if no namespace given', () => {
    expect(() => getQSConfig()).toThrow();
  });

  test('should build configured QS config object', () => {
    const defaults = {
      page: 1,
      page_size: 15,
    };
    expect(getQSConfig('inventory', defaults)).toEqual({
      namespace: 'inventory',
      defaultParams: { page: 1, page_size: 15 },
      integerFields: ['page', 'page_size'],
    });
  });

  describe('parseNamespacedQueryString', () => {
    test('should get query params', () => {
      const config = {
        namespace: null,
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?foo=bar&page=3';
      expect(parseNamespacedQueryString(config, query)).toEqual({
        foo: 'bar',
        page: 3,
        page_size: 15,
      });
    });

    test('should get query params with correct integer fields', () => {
      const config = {
        namespace: null,
        defaultParams: {},
        integerFields: ['page', 'foo'],
      };
      const query = '?foo=4&bar=5';
      expect(parseNamespacedQueryString(config, query)).toEqual({
        foo: 4,
        bar: '5',
      });
    });

    test('should get namespaced query params', () => {
      const config = {
        namespace: 'inventory',
        defaultParams: { page: 1, page_size: 5 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?inventory.page=2&inventory.order_by=name&other=15';
      expect(parseNamespacedQueryString(config, query)).toEqual({
        page: 2,
        order_by: 'name',
        page_size: 5,
      });
    });

    test('should exclude other namespaced query params', () => {
      const config = {
        namespace: 'inventory',
        defaultParams: { page: 1, page_size: 5 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?inventory.page=2&inventory.order_by=name&foo.other=15';
      expect(parseNamespacedQueryString(config, query)).toEqual({
        page: 2,
        order_by: 'name',
        page_size: 5,
      });
    });

    test('should exclude defaults if includeDefaults is false', () => {
      const config = {
        namespace: null,
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?foo=bar&page=3';
      expect(parseNamespacedQueryString(config, query, false)).toEqual({
        foo: 'bar',
        page: 3,
      });
    });
  });

  describe('encodeNamespacedQueryString', () => {
    test('should encode params without namespace', () => {
      const config = {
        namespace: null,
        defaultParams: { page: 1, page_size: 5 },
        integerFields: ['page', 'page_size'],
      };
      const params = {
        page: 1,
        order_by: 'name',
      };
      const qs = 'order_by=name&page=1';
      expect(encodeNamespacedQueryString(config, params)).toEqual(qs);
    });

    test('should encode params with namespace', () => {
      const config = {
        namespace: 'inventory',
        defaultParams: { page: 1, page_size: 5 },
        integerFields: ['page', 'page_size'],
      };
      const params = {
        page: 1,
        order_by: 'name',
      };
      const qs = 'inventory.order_by=name&inventory.page=1';
      expect(encodeNamespacedQueryString(config, params)).toEqual(qs);
    });
  });

  describe('updateNamespacedQueryString', () => {
    test('should return current values', () => {
      const qs = '?foo=bar&inventory.page=1';
      const updated = updateNamespacedQueryString({}, qs, {});
      expect(updated).toEqual('foo=bar&inventory.page=1');
    });

    test('should update new values', () => {
      const qs = '?foo=bar&inventory.page=1';
      const updated = updateNamespacedQueryString({}, qs, { foo: 'baz' });
      expect(updated).toEqual('foo=baz&inventory.page=1');
    });

    test('should add new values', () => {
      const qs = '?foo=bar&inventory.page=1';
      const updated = updateNamespacedQueryString({}, qs, { page: 5 });
      expect(updated).toEqual('foo=bar&inventory.page=1&page=5');
    });

    test('should update namespaced values', () => {
      const qs = '?foo=bar&inventory.page=1';
      const config = { namespace: 'inventory' };
      const updated = updateNamespacedQueryString(config, qs, { page: 2 });
      expect(updated).toEqual('foo=bar&inventory.page=2');
    });
  });
});
