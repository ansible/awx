import {
  removeDefaultParams,
  removeNamespacedKeys,
  toHostFilter,
  toQueryString,
  toSearchParams,
  modifyHostFilter,
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
  test('should take a host filter string separated by or and return search params object with or', () => {
    string = 'foo=bar or foo=baz';
    paramsObject = {
      or__foo: ['bar', 'baz'],
    };
    expect(toSearchParams(string)).toEqual(paramsObject);
  });
  test('should take a host filter string with or and return search params object with or', () => {
    string = 'or__foo=1&or__foo=2';
    paramsObject = {
      or__foo: ['1', '2'],
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
  test('should return a host filter with mixed conditionals', () => {
    const object = {
      or__name__contains: 'bar',
      or__name__iexact: 'foo',
      enabled: 'true',
      name__contains: 'x',
      or__name: 'foo',
    };
    expect(toHostFilter(object)).toEqual(
      'enabled=true and name__contains=x or name=foo or name__contains=bar or name__iexact=foo'
    );
  });

  test('should return a host filter with escaped string', () => {
    const object = {
      or__description__contains: 'bar biz',
      enabled: 'true',
      name__contains: 'x',
      or__name: 'foo',
    };
    expect(toHostFilter(object)).toEqual(
      'enabled=true and name__contains=x or description__contains="bar biz" or name=foo'
    );
  });

  test('should return a host filter with and conditional', () => {
    const object = {
      enabled: 'true',
      name__contains: 'x',
    };
    expect(toHostFilter(object)).toEqual('enabled=true and name__contains=x');
  });

  test('should return a host filter with or conditional', () => {
    const object = {
      or__name__contains: 'bar',
      or__name__iexact: 'foo',
      or__name: 'foo',
    };
    expect(toHostFilter(object)).toEqual(
      'name=foo or name__contains=bar or name__iexact=foo'
    );
  });

  test('should return a host filter with or conditional when value is array', () => {
    const object = {
      or__groups__id: ['1', '2'],
    };
    expect(toHostFilter(object)).toEqual('groups__id=1 or groups__id=2');
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

describe('modifyHostFilter', () => {
  test('should modify host_filter', () => {
    const object = {
      foo: ['bar', 'baz', 'qux'],
      apat: 'lima',
      page: 10,
      order_by: '-name',
    };
    expect(
      modifyHostFilter(
        'host_filter=ansible_facts__ansible_lo__ipv6[]__scope="host"',
        object
      )
    ).toEqual({
      apat: 'lima',
      foo: ['bar', 'baz', 'qux'],
      host_filter: 'ansible_facts__ansible_lo__ipv6[]__scope="host"',
      order_by: '-name',
      page: 10,
    });
  });
  test('should not modify host_filter', () => {
    const object = { groups__name__icontains: '1' };
    expect(
      modifyHostFilter('groups__name__icontains=1', {
        groups__name__icontains: '1',
      })
    ).toEqual(object);
  });
});
