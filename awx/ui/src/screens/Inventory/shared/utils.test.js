import parseHostFilter from './utils';

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
