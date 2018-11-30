import getTabName from '../../../src/pages/Organizations/utils';

describe('getTabName', () => {
  test('returns tab name', () => {
    expect(getTabName('details')).toBe('Details');
    expect(getTabName('users')).toBe('Users');
    expect(getTabName('teams')).toBe('Teams');
    expect(getTabName('admins')).toBe('Admins');
    expect(getTabName('notifications')).toBe('Notifications');
    expect(getTabName('unknown')).toBe('');
    expect(getTabName()).toBe('');
  });
});
