import getRouteConfig, { verifyUserRole } from './routeConfig';

describe('verify user role', () => {
  test('verify super user`', () => {
    const user = {
      isSuperUser: true,
      isSystemAuditor: false,
      isOrgAdmin: true,
      isNotifAdmin: false,
    };

    expect(verifyUserRole(user)).toEqual('isSuperUser');
  });

  test('verify system auditor`', () => {
    const user = {
      isSuperUser: false,
      isSystemAuditor: true,
      isOrgAdmin: false,
      isNotifAdmin: false,
    };

    expect(verifyUserRole(user)).toEqual('isSuperUser');
  });

  test('verify org admin', () => {
    const user = {
      isSuperUser: false,
      isSystemAuditor: false,
      isOrgAdmin: true,
      isNotifAdmin: false,
    };

    expect(verifyUserRole(user)).toEqual('isVisibleOrgAdmin');
  });

  test('verify org admin and notification admin ', () => {
    const user = {
      isSuperUser: false,
      isSystemAuditor: false,
      isOrgAdmin: true,
      isNotifAdmin: true,
    };

    expect(verifyUserRole(user)).toEqual('isVisibleOrgAdmin');
  });

  test('verify notification admin ', () => {
    const user = {
      isSuperUser: false,
      isSystemAuditor: false,
      isOrgAdmin: false,
      isNotifAdmin: true,
    };

    expect(verifyUserRole(user)).toEqual('isVisibleNotifAdmin');
  });

  test('verify normal user', () => {
    const user = {
      isSuperUser: false,
      isSystemAuditor: false,
      isOrgAdmin: false,
      isNotifAdmin: false,
    };

    expect(verifyUserRole(user)).toEqual('isVisibleNormalUser');
  });
});

describe('getRouteConfig', () => {
  const i18n = { _: val => val };
  test('verify super user', () => {
    const user = {
      isSuperUser: true,
      isSystemAuditor: false,
      isOrgAdmin: true,
      isNotifAdmin: true,
    };

    expect(getRouteConfig(i18n, user).length).toEqual(5);
  });

  test('verify auditor user', () => {
    const user = {
      isSuperUser: false,
      isSystemAuditor: true,
      isOrgAdmin: false,
      isNotifAdmin: false,
    };

    expect(getRouteConfig(i18n, user).length).toEqual(5);
  });

  test('verify normal user', () => {
    const user = {
      isSuperUser: false,
      isSystemAuditor: false,
      isOrgAdmin: false,
      isNotifAdmin: false,
    };

    expect(getRouteConfig(i18n, user).length).toEqual(3);
  });

  test('verify org admin', () => {
    const user = {
      isSuperUser: false,
      isSystemAuditor: false,
      isOrgAdmin: true,
      isNotifAdmin: false,
    };

    expect(getRouteConfig(i18n, user).length).toEqual(4);
  });

  test('verify org admin and notification admin', () => {
    const user = {
      isSuperUser: false,
      isSystemAuditor: false,
      isOrgAdmin: true,
      isNotifAdmin: true,
    };

    expect(getRouteConfig(i18n, user).length).toEqual(4);
  });
});
