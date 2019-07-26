import {
  encodeQueryString,
  encodeNonDefaultQueryString,
  parseQueryString,
  getQSConfig,
  addParams,
  removeParams,
} from './qs';

describe('qs (qs.js)', () => {
  describe('encodeQueryString', () => {
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
  });

  describe('encodeNonDefaultQueryString', () => {
    const config = {
      namespace: null,
      defaultParams: { page: 1, page_size: 5, order_by: 'name' },
      integerFields: ['page'],
    };

    test('encodeNonDefaultQueryString returns the expected queryString', () => {
      [
        [null, ''],
        [{}, ''],
        [{ order_by: 'name', page: 1, page_size: 5 }, ''],
        [{ order_by: '-name', page: 1, page_size: 5 }, 'order_by=-name'],
        [
          { order_by: '-name', page: 3, page_size: 10 },
          'order_by=-name&page=3&page_size=10',
        ],
        [
          { order_by: '-name', page: 3, page_size: 10, foo: 'bar' },
          'foo=bar&order_by=-name&page=3&page_size=10',
        ],
      ].forEach(([params, expectedQueryString]) => {
        const actualQueryString = encodeNonDefaultQueryString(config, params);

        expect(actualQueryString).toEqual(expectedQueryString);
      });
    });

    test('encodeNonDefaultQueryString omits null values', () => {
      const vals = {
        order_by: 'foo',
        page: null,
      };
      expect(encodeNonDefaultQueryString(config, vals)).toEqual('order_by=foo');
    });
  });

  describe('getQSConfig', () => {
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
  });

  describe('parseQueryString', () => {
    test('should get query params', () => {
      const config = {
        namespace: null,
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?baz=bar&page=3';
      expect(parseQueryString(config, query)).toEqual({
        baz: 'bar',
        page: 3,
        page_size: 15,
      });
    });

    test('should return namespaced defaults if empty query string passed', () => {
      const config = {
        namespace: 'foo',
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const query = '';
      expect(parseQueryString(config, query)).toEqual({
        page: 1,
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
      expect(parseQueryString(config, query)).toEqual({
        foo: 4,
        bar: '5',
      });
    });

    test('should decode parsed params', () => {
      const config = {
        namespace: null,
        defaultParams: {},
        integerFields: ['page'],
      };
      const query = '?foo=bar%20baz';
      expect(parseQueryString(config, query)).toEqual({
        foo: 'bar baz',
      });
    });

    test('should get namespaced query params', () => {
      const config = {
        namespace: 'inventory',
        defaultParams: { page: 1, page_size: 5 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?inventory.page=2&inventory.order_by=name&other=15';
      expect(parseQueryString(config, query)).toEqual({
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
      expect(parseQueryString(config, query)).toEqual({
        page: 2,
        order_by: 'name',
        page_size: 5,
      });
    });

    test('should exclude other namespaced default query params', () => {
      const config = {
        namespace: 'inventory',
        defaultParams: { page: 1, page_size: 5 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?foo.page=2&inventory.order_by=name&foo.other=15';
      expect(parseQueryString(config, query)).toEqual({
        page: 1,
        order_by: 'name',
        page_size: 5,
      });
    });

    test('should add duplicate non-default params as array', () => {
      const config = {
        namespace: null,
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?baz=bar&baz=boo&page=3';
      expect(parseQueryString(config, query)).toEqual({
        baz: ['bar', 'boo'],
        page: 3,
        page_size: 15,
      });
    });

    test('should add duplicate namespaced non-default params as array', () => {
      const config = {
        namespace: 'bee',
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?bee.baz=bar&bee.baz=boo&bee.page=3';
      expect(parseQueryString(config, query)).toEqual({
        baz: ['bar', 'boo'],
        page: 3,
        page_size: 15,
      });
    });
  });

  describe('addParams', () => {
    test('should add query params', () => {
      const config = {
        namespace: null,
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?baz=bar&page=3';
      const newParams = { bag: 'boom' };
      expect(addParams(config, query, newParams)).toEqual({
        baz: 'bar',
        bag: 'boom',
        page: 3,
        page_size: 15,
      });
    });

    test('should add query params with duplicates', () => {
      const config = {
        namespace: null,
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?baz=bar&baz=bang&page=3';
      const newParams = { baz: 'boom' };
      expect(addParams(config, query, newParams)).toEqual({
        baz: ['bar', 'bang', 'boom'],
        page: 3,
        page_size: 15,
      });
    });

    test('should replace query params that are defaults', () => {
      const config = {
        namespace: null,
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?baz=bar&baz=bang&page=3';
      const newParams = { page: 5 };
      expect(addParams(config, query, newParams)).toEqual({
        baz: ['bar', 'bang'],
        page: 5,
        page_size: 15,
      });
    });

    test('should add multiple params', () => {
      const config = {
        namespace: null,
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?baz=bar&baz=bang&page=3';
      const newParams = { baz: 'bust', pat: 'pal' };
      expect(addParams(config, query, newParams)).toEqual({
        baz: ['bar', 'bang', 'bust'],
        pat: 'pal',
        page: 3,
        page_size: 15,
      });
    });

    test('should add namespaced query params', () => {
      const config = {
        namespace: 'item',
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?item.baz=bar&item.page=3';
      const newParams = { bag: 'boom' };
      expect(addParams(config, query, newParams)).toEqual({
        baz: 'bar',
        bag: 'boom',
        page: 3,
        page_size: 15,
      });
    });

    test('should not include other namespaced query params when adding', () => {
      const config = {
        namespace: 'item',
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?item.baz=bar&foo.page=3';
      const newParams = { bag: 'boom' };
      expect(addParams(config, query, newParams)).toEqual({
        baz: 'bar',
        bag: 'boom',
        page: 1,
        page_size: 15,
      });
    });

    test('should add namespaced query params with duplicates', () => {
      const config = {
        namespace: 'item',
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?item.baz=bar&item.baz=bang&item.page=3';
      const newParams = { baz: 'boom' };
      expect(addParams(config, query, newParams)).toEqual({
        baz: ['bar', 'bang', 'boom'],
        page: 3,
        page_size: 15,
      });
    });

    test('should replace namespaced query params that are defaults', () => {
      const config = {
        namespace: 'item',
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?item.baz=bar&item.baz=bang&item.page=3';
      const newParams = { page: 5 };
      expect(addParams(config, query, newParams)).toEqual({
        baz: ['bar', 'bang'],
        page: 5,
        page_size: 15,
      });
    });

    test('should add multiple namespaced params', () => {
      const config = {
        namespace: 'item',
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?item.baz=bar&item.baz=bang&item.page=3';
      const newParams = { baz: 'bust', pat: 'pal' };
      expect(addParams(config, query, newParams)).toEqual({
        baz: ['bar', 'bang', 'bust'],
        pat: 'pal',
        page: 3,
        page_size: 15,
      });
    });
  });

  describe('removeParams', () => {
    test('should remove query params', () => {
      const config = {
        namespace: null,
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?baz=bar&page=3&bag=boom';
      const newParams = { bag: 'boom' };
      expect(removeParams(config, query, newParams)).toEqual({
        baz: 'bar',
        page: 3,
        page_size: 15,
      });
    });

    test('should remove query params with duplicates (array -> string)', () => {
      const config = {
        namespace: null,
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?baz=bar&baz=bang&page=3';
      const newParams = { baz: 'bar' };
      expect(removeParams(config, query, newParams)).toEqual({
        baz: 'bang',
        page: 3,
        page_size: 15,
      });
    });

    test('should remove query params with duplicates (array -> smaller array)', () => {
      const config = {
        namespace: null,
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?baz=bar&baz=bang&baz=bust&page=3';
      const newParams = { baz: 'bar' };
      expect(removeParams(config, query, newParams)).toEqual({
        baz: ['bang', 'bust'],
        page: 3,
        page_size: 15,
      });
    });

    test('should reset query params that have default keys back to default values', () => {
      const config = {
        namespace: null,
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?baz=bar&baz=bang&page=3';
      const newParams = { page: 3 };
      expect(removeParams(config, query, newParams)).toEqual({
        baz: ['bar', 'bang'],
        page: 1,
        page_size: 15,
      });
    });

    test('should remove multiple params', () => {
      const config = {
        namespace: null,
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?baz=bar&baz=bang&baz=bust&pat=pal&page=3';
      const newParams = { baz: 'bust', pat: 'pal' };
      expect(removeParams(config, query, newParams)).toEqual({
        baz: ['bar', 'bang'],
        page: 3,
        page_size: 15,
      });
    });

    test('should remove namespaced query params', () => {
      const config = {
        namespace: 'item',
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?item.baz=bar&item.page=3';
      const newParams = { baz: 'bar' };
      expect(removeParams(config, query, newParams)).toEqual({
        page: 3,
        page_size: 15,
      });
    });

    test('should not include other namespaced query params when removing', () => {
      const config = {
        namespace: 'item',
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?item.baz=bar&foo.page=3';
      const newParams = { baz: 'bar' };
      expect(removeParams(config, query, newParams)).toEqual({
        page: 1,
        page_size: 15,
      });
    });

    test('should remove namespaced query params with duplicates (array -> string)', () => {
      const config = {
        namespace: 'item',
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?item.baz=bar&item.baz=bang&item.page=3';
      const newParams = { baz: 'bar' };
      expect(removeParams(config, query, newParams)).toEqual({
        baz: 'bang',
        page: 3,
        page_size: 15,
      });
    });

    test('should remove namespaced query params with duplicates (array -> smaller array)', () => {
      const config = {
        namespace: 'item',
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?item.baz=bar&item.baz=bang&item.baz=bust&item.page=3';
      const newParams = { baz: 'bar' };
      expect(removeParams(config, query, newParams)).toEqual({
        baz: ['bang', 'bust'],
        page: 3,
        page_size: 15,
      });
    });

    test('should reset namespaced query params that have default keys back to default values', () => {
      const config = {
        namespace: 'item',
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?item.baz=bar&item.baz=bang&item.page=3';
      const newParams = { page: 3 };
      expect(removeParams(config, query, newParams)).toEqual({
        baz: ['bar', 'bang'],
        page: 1,
        page_size: 15,
      });
    });

    test('should remove multiple namespaced params', () => {
      const config = {
        namespace: 'item',
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const query =
        '?item.baz=bar&item.baz=bang&item.baz=bust&item.pat=pal&item.page=3';
      const newParams = { baz: 'bust', pat: 'pal' };
      expect(removeParams(config, query, newParams)).toEqual({
        baz: ['bar', 'bang'],
        page: 3,
        page_size: 15,
      });
    });
  });
});
