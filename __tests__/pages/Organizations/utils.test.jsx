import getTabName from '../../../src/pages/Organizations/utils';

describe('getTabName', () => {
  test('returns tab name', () => {
    expect(getTabName('details')).toBe('Details');
    expect(getTabName('access')).toBe('Access');
    expect(getTabName('teams')).toBe('Teams');
    expect(getTabName('notifications')).toBe('Notifications');
    expect(getTabName('unknown')).toBe('');
    expect(getTabName()).toBe('');
  });
});
