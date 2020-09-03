import {
  removeDefaultParams,
  removeNamespacedKeys,
  toHostFilter,
  toQueryString,
  toSearchParams,
} from './HostFilterUtils';

const QS_CONFIG = {
  namespace: 'mock',
  defaultParams: { page: 1, page_size: 5, order_by: 'name' },
  integerFields: ['page', 'page_size', 'id', 'inventory'],
};

describe('toSearchParams', () => {
  let string;
  let paramsObject;

  test('should return an empty object', () => {
    expect(toSearchParams(undefined)).toEqual({});
    expect(toSearchParams('')).toEqual({});
  });
  test('should take a query string and return search params object', () => {
    string = '?foo=bar';
    paramsObject = { foo: 'bar' };
    expect(toSearchParams(string)).toEqual(paramsObject);
  });
  test('should take a host filter string and return search params object', () => {
    string = 'foo=bar and foo=baz and foo=qux and isa=sampu';
    paramsObject = {
      foo: ['bar', 'baz', 'qux'],
      isa: 'sampu',
    };
    expect(toSearchParams(string)).toEqual(paramsObject);
  });
});

describe('toQueryString', () => {
  test('should return an empty string', () => {
    expect(toQueryString(QS_CONFIG, undefined)).toEqual('');
  });
  test('should return namespaced query string with a single key-value pair', () => {
    const object = {
      foo: 'bar',
    };
    expect(toQueryString(QS_CONFIG, object)).toEqual('mock.foo=bar');
  });
  test('should return namespaced query string with multiple values per key', () => {
    const object = {
      foo: ['bar', 'baz'],
    };
    expect(toQueryString(QS_CONFIG, object)).toEqual(
      'mock.foo=bar&mock.foo=baz'
    );
  });
  test('should return namespaced query string with multiple key-value pairs', () => {
    const object = {
      foo: ['bar', 'baz', 'qux'],
      isa: 'sampu',
    };
    expect(toQueryString(QS_CONFIG, object)).toEqual(
      'mock.foo=bar&mock.foo=baz&mock.foo=qux&mock.isa=sampu'
    );
  });
});

describe('toHostFilter', () => {
  test('should return an empty string', () => {
    expect(toHostFilter(undefined)).toEqual('');
  });
  test('should return a host filter string', () => {
    const object = {
      isa: '2',
      tatlo: ['foo', 'bar', 'baz'],
    };
    expect(toHostFilter(object)).toEqual(
      'isa=2 and tatlo=foo and tatlo=bar and tatlo=baz'
    );
  });
});

describe('removeNamespacedKeys', () => {
  test('should return an empty object', () => {
    expect(removeNamespacedKeys(QS_CONFIG, undefined)).toEqual({});
  });
  test('should remove namespace from keys', () => {
    expect(removeNamespacedKeys(QS_CONFIG, { 'mock.foo': 'bar' })).toEqual({
      foo: 'bar',
    });
  });
});

describe('removeDefaultParams', () => {
  test('should return an empty object', () => {
    expect(removeDefaultParams(QS_CONFIG, undefined)).toEqual({});
  });
  test('should remove default params', () => {
    const object = {
      foo: ['bar', 'baz', 'qux'],
      apat: 'lima',
      page: 10,
      order_by: '-name',
    };
    expect(removeDefaultParams(QS_CONFIG, object)).toEqual({
      foo: ['bar', 'baz', 'qux'],
      apat: 'lima',
    });
  });
});
