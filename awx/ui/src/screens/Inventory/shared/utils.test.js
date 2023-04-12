import parseHostFilter, { getInventoryPath } from './utils';

describe('parseHostFilter', () => {
  test('parse host filter', () => {
    expect(
      parseHostFilter({
        host_filter:
          'host_filter=ansible_facts__ansible_processor[]="GenuineIntel"',
        name: 'Foo',
      })
    ).toEqual({
      host_filter: 'ansible_facts__ansible_processor[]="GenuineIntel"',
      name: 'Foo',
    });
  });
  test('do not parse host filter', () => {
    expect(parseHostFilter({ name: 'Foo' })).toEqual({
      name: 'Foo',
    });
  });
});

describe('getInventoryPath', () => {
  test('should return inventory path', () => {
    expect(getInventoryPath({ id: 1, kind: '' })).toMatch(
      '/inventories/inventory/1'
    );
  });
  test('should return smart inventory path', () => {
    expect(getInventoryPath({ id: 2, kind: 'smart' })).toMatch(
      '/inventories/smart_inventory/2'
    );
  });
  test('should return constructed inventory path', () => {
    expect(getInventoryPath({ id: 3, kind: 'constructed' })).toMatch(
      '/inventories/constructed_inventory/3'
    );
  });
});
