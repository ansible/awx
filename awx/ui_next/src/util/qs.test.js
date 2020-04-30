import {
  encodeQueryString,
  encodeNonDefaultQueryString,
  parseQueryString,
  getQSConfig,
  removeParams,
  _stringToObject,
  _addDefaultsToObject,
  mergeParams,
  replaceParams,
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

    test('should encode array params', () => {
      const vals = {
        foo: ['one', 'two', 'three'],
      };
      expect(encodeQueryString(vals)).toEqual('foo=one&foo=two&foo=three');
    });
  });

  describe('encodeNonDefaultQueryString', () => {
    const config = {
      namespace: null,
      defaultParams: { page: 1, page_size: 5, order_by: 'name' },
      integerFields: ['page'],
    };

    test('should return the expected queryString', () => {
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

    test('should omit null values', () => {
      const vals = {
        order_by: 'foo',
        page: null,
      };
      expect(encodeNonDefaultQueryString(config, vals)).toEqual('order_by=foo');
    });

    test('should namespace encoded params', () => {
      const conf = {
        namespace: 'item',
        defaultParams: { page: 1 },
      };
      const params = {
        page: 1,
        foo: 'bar',
      };
      expect(encodeNonDefaultQueryString(conf, params)).toEqual('item.foo=bar');
    });

    test('should handle array values', () => {
      const vals = {
        foo: ['one', 'two'],
        bar: ['alpha', 'beta'],
      };
      const conf = {
        defaultParams: {
          foo: ['one', 'two'],
        },
      };
      expect(encodeNonDefaultQueryString(conf, vals)).toEqual(
        'bar=alpha&bar=beta'
      );
    });
  });

  describe('getQSConfig', () => {
    test('should get default QS config object', () => {
      expect(getQSConfig('organization')).toEqual({
        namespace: 'organization',
        defaultParams: { page: 1, page_size: 5, order_by: 'name' },
        integerFields: ['page', 'page_size'],
        dateFields: ['modified', 'created'],
      });
    });

    test('should set order_by in defaultParams if it is not passed', () => {
      expect(
        getQSConfig('organization', {
          page: 1,
          page_size: 5,
        })
      ).toEqual({
        namespace: 'organization',
        defaultParams: { page: 1, page_size: 5, order_by: 'name' },
        integerFields: ['page', 'page_size'],
        dateFields: ['modified', 'created'],
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
        defaultParams: { page: 1, page_size: 15, order_by: 'name' },
        integerFields: ['page', 'page_size'],
        dateFields: ['modified', 'created'],
      });
    });
  });

  describe('parseQueryString', () => {
    test('should get query params', () => {
      const config = {
        namespace: 'item',
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?item.baz=bar&item.page=3';
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
        namespace: 'item',
        defaultParams: {},
        integerFields: ['page', 'foo'],
      };
      const query = '?item.foo=4&item.bar=5';
      expect(parseQueryString(config, query)).toEqual({
        foo: 4,
        bar: '5',
      });
    });

    test('should decode parsed params', () => {
      const config = {
        namespace: 'item',
        defaultParams: {},
        integerFields: ['page'],
      };
      const query = '?item.foo=bar%20baz';
      expect(parseQueryString(config, query)).toEqual({
        foo: 'bar baz',
      });
    });

    test('should decode param keys', () => {
      const config = {
        namespace: 'item',
        defaultParams: {},
        integerFields: ['page'],
      };
      const query = '?item.foo%20bar=baz';
      expect(parseQueryString(config, query)).toEqual({
        'foo bar': 'baz',
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
        namespace: 'item',
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?item.baz=bar&item.baz=boo&item.page=3';
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

    test('should parse long arrays', () => {
      const config = {
        namespace: 'item',
      };
      const query = '?item.baz=one&item.baz=two&item.baz=three';
      expect(parseQueryString(config, query)).toEqual({
        baz: ['one', 'two', 'three'],
      });
    });

    test('should handle non-namespaced params', () => {
      const config = {
        namespace: null,
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?item.baz=bar&page=3';
      expect(parseQueryString(config, query)).toEqual({
        page: 3,
        page_size: 15,
      });
    });

    test('should parse empty string values', () => {
      const config = {
        namespace: 'bee',
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const query = '?bee.baz=bar&bee.or__source=';
      expect(parseQueryString(config, query)).toEqual({
        baz: 'bar',
        page: 1,
        page_size: 15,
        or__source: '',
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
      const oldParams = { baz: 'bar', page: 3, bag: 'boom', page_size: 15 };
      const toRemove = { bag: 'boom' };
      expect(removeParams(config, oldParams, toRemove)).toEqual({
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
      const oldParams = { baz: ['bar', 'bang'], page: 3, page_size: 15 };
      const toRemove = { baz: 'bar' };
      expect(removeParams(config, oldParams, toRemove)).toEqual({
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
      const oldParams = {
        baz: ['bar', 'bang', 'bust'],
        page: 3,
        page_size: 15,
      };
      const toRemove = { baz: 'bar' };
      expect(removeParams(config, oldParams, toRemove)).toEqual({
        baz: ['bang', 'bust'],
        page: 3,
        page_size: 15,
      });
    });

    test('should remove multiple values from query params (array -> smaller array)', () => {
      const config = {
        namespace: null,
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const oldParams = {
        baz: ['bar', 'bang', 'bust'],
        page: 3,
        page_size: 15,
      };
      const toRemove = { baz: ['bang', 'bar'] };
      expect(removeParams(config, oldParams, toRemove)).toEqual({
        baz: 'bust',
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
      const oldParams = { baz: ['bar', 'bang'], page: 3, page_size: 15 };
      const toRemove = { page: 3 };
      expect(removeParams(config, oldParams, toRemove)).toEqual({
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
      const oldParams = {
        baz: ['bar', 'bang', 'bust'],
        pat: 'pal',
        page: 3,
        page_size: 15,
      };
      const toRemove = { baz: 'bust', pat: 'pal' };
      expect(removeParams(config, oldParams, toRemove)).toEqual({
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
      const oldParams = { baz: 'bar', page: 3, page_size: 15 };
      const toRemove = { baz: 'bar' };
      expect(removeParams(config, oldParams, toRemove)).toEqual({
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
      const oldParams = { baz: 'bar', page: 1, page_size: 15 };
      const toRemove = { baz: 'bar' };
      expect(removeParams(config, oldParams, toRemove)).toEqual({
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
      const oldParams = { baz: ['bar', 'bang'], page: 3, page_size: 15 };
      const toRemove = { baz: 'bar' };
      expect(removeParams(config, oldParams, toRemove)).toEqual({
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
      const oldParams = {
        baz: ['bar', 'bang', 'bust'],
        page: 3,
        page_size: 15,
      };
      const toRemove = { baz: 'bar' };
      expect(removeParams(config, oldParams, toRemove)).toEqual({
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
      const oldParams = { baz: ['bar', 'bang'], page: 3, page_size: 15 };
      const toRemove = { page: 3 };
      expect(removeParams(config, oldParams, toRemove)).toEqual({
        baz: ['bar', 'bang'],
        page: 1,
        page_size: 15,
      });
    });

    test('should retain long array values', () => {
      const config = {
        namespace: 'item',
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const oldParams = {
        baz: ['one', 'two', 'three'],
        page: 3,
        bag: 'boom',
        page_size: 15,
      };
      const toRemove = { bag: 'boom' };
      expect(removeParams(config, oldParams, toRemove)).toEqual({
        baz: ['one', 'two', 'three'],
        page: 3,
        page_size: 15,
      });
    });

    test('should remove multiple namespaced params', () => {
      const config = {
        namespace: 'item',
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const oldParams = {
        baz: ['bar', 'bang', 'bust'],
        pat: 'pal',
        page: 3,
        page_size: 15,
      };
      const toRemove = { baz: 'bust', pat: 'pal' };
      expect(removeParams(config, oldParams, toRemove)).toEqual({
        baz: ['bar', 'bang'],
        page: 3,
        page_size: 15,
      });
    });

    test('should retain empty string', () => {
      const config = {
        namespace: null,
        defaultParams: { page: 1, page_size: 15 },
        integerFields: ['page', 'page_size'],
      };
      const oldParams = { baz: '', page: 3, bag: 'boom', page_size: 15 };
      const toRemove = { bag: 'boom' };
      expect(removeParams(config, oldParams, toRemove)).toEqual({
        baz: '',
        page: 3,
        page_size: 15,
      });
    });
  });

  describe('_stringToObject', () => {
    test('should convert to object', () => {
      const config = { namespace: 'unit' };
      expect(_stringToObject(config, '?unit.foo=bar&unit.baz=bam')).toEqual({
        foo: 'bar',
        baz: 'bam',
      });
    });

    test('should convert duplicated keys to array', () => {
      const config = { namespace: 'unit' };
      expect(_stringToObject(config, '?unit.foo=bar&unit.foo=bam')).toEqual({
        foo: ['bar', 'bam'],
      });
    });

    test('should omit keys from other namespaces', () => {
      const config = { namespace: 'unit' };
      expect(
        _stringToObject(config, '?unit.foo=bar&other.bar=bam&one=two')
      ).toEqual({
        foo: 'bar',
      });
    });

    test('should convert numbers to correct type', () => {
      const config = {
        namespace: 'unit',
        integerFields: ['page'],
      };
      expect(_stringToObject(config, '?unit.page=3')).toEqual({
        page: 3,
      });
    });
  });

  describe('_addDefaultsToObject', () => {
    test('should add missing default values', () => {
      const config = {
        defaultParams: { page: 1, page_size: 5, order_by: 'name' },
      };
      expect(_addDefaultsToObject(config, {})).toEqual({
        page: 1,
        page_size: 5,
        order_by: 'name',
      });
    });

    test('should not override existing params', () => {
      const config = {
        defaultParams: { page: 1, page_size: 5, order_by: 'name' },
      };
      const params = {
        page: 2,
        order_by: 'date_created',
      };
      expect(_addDefaultsToObject(config, params)).toEqual({
        page: 2,
        page_size: 5,
        order_by: 'date_created',
      });
    });

    test('should handle missing defaultParams', () => {
      const params = {
        page: 2,
        order_by: 'date_created',
      };
      expect(_addDefaultsToObject({}, params)).toEqual({
        page: 2,
        order_by: 'date_created',
      });
    });
  });

  describe('mergeParams', () => {
    it('should merge param into an array', () => {
      const oldParams = {
        foo: 'one',
      };
      const newParams = {
        foo: 'two',
      };
      expect(mergeParams(oldParams, newParams)).toEqual({
        foo: ['one', 'two'],
      });
    });

    it('should not remove empty string values', () => {
      const oldParams = {
        foo: '',
      };
      const newParams = {
        foo: 'two',
      };
      expect(mergeParams(oldParams, newParams)).toEqual({
        foo: ['', 'two'],
      });

      const oldParams2 = {
        foo: 'one',
      };
      const newParams2 = {
        foo: '',
      };
      expect(mergeParams(oldParams2, newParams2)).toEqual({
        foo: ['one', ''],
      });
    });

    it('should retain unaltered params', () => {
      const oldParams = {
        foo: 'one',
        bar: 'baz',
      };
      const newParams = {
        foo: 'two',
      };
      expect(mergeParams(oldParams, newParams)).toEqual({
        foo: ['one', 'two'],
        bar: 'baz',
      });
    });

    it('should gather params from both objects', () => {
      const oldParams = {
        one: 'one',
      };
      const newParams = {
        two: 'two',
      };
      expect(mergeParams(oldParams, newParams)).toEqual({
        one: 'one',
        two: 'two',
      });
    });

    it('should append value to existing array', () => {
      const oldParams = {
        foo: ['one', 'two'],
      };
      const newParams = {
        foo: 'three',
      };
      expect(mergeParams(oldParams, newParams)).toEqual({
        foo: ['one', 'two', 'three'],
      });
    });

    it('should append array to existing value', () => {
      const oldParams = {
        foo: 'one',
      };
      const newParams = {
        foo: ['two', 'three'],
      };
      expect(mergeParams(oldParams, newParams)).toEqual({
        foo: ['one', 'two', 'three'],
      });
    });

    it('should merge two arrays', () => {
      const oldParams = {
        foo: ['one', 'two'],
      };
      const newParams = {
        foo: ['three', 'four'],
      };
      expect(mergeParams(oldParams, newParams)).toEqual({
        foo: ['one', 'two', 'three', 'four'],
      });
    });

    it('should prevent exact duplicates', () => {
      const oldParams = { foo: 'one' };
      const newParams = { foo: 'one' };
      expect(mergeParams(oldParams, newParams)).toEqual({ foo: 'one' });
    });

    it('should prevent exact duplicates in arrays', () => {
      const oldParams = { foo: ['one', 'three'] };
      const newParams = { foo: ['one', 'two'] };
      expect(mergeParams(oldParams, newParams)).toEqual({
        foo: ['one', 'three', 'two'],
      });
    });

    it('should add multiple params', () => {
      const oldParams = { baz: ['bar', 'bang'], page: 3, page_size: 15 };
      const newParams = { baz: 'bust', pat: 'pal' };
      expect(mergeParams(oldParams, newParams)).toEqual({
        baz: ['bar', 'bang', 'bust'],
        pat: 'pal',
        page: 3,
        page_size: 15,
      });
    });
  });

  describe('replaceParams', () => {
    it('should collect params into one object', () => {
      const oldParams = { foo: 'one' };
      const newParams = { bar: 'two' };
      expect(replaceParams(oldParams, newParams)).toEqual({
        foo: 'one',
        bar: 'two',
      });
    });

    it('should retain unaltered params', () => {
      const oldParams = {
        foo: 'one',
        bar: 'baz',
      };
      const newParams = { foo: 'two' };
      expect(replaceParams(oldParams, newParams)).toEqual({
        foo: 'two',
        bar: 'baz',
      });
    });

    it('should override old values with new ones', () => {
      const oldParams = {
        foo: 'one',
        bar: 'three',
      };
      const newParams = {
        foo: 'two',
        baz: 'four',
      };
      expect(replaceParams(oldParams, newParams)).toEqual({
        foo: 'two',
        bar: 'three',
        baz: 'four',
      });
    });

    it('should handle exact duplicates', () => {
      const oldParams = { foo: 'one' };
      const newParams = { foo: 'one', bar: 'two' };
      expect(replaceParams(oldParams, newParams)).toEqual({
        foo: 'one',
        bar: 'two',
      });
    });
  });
});
