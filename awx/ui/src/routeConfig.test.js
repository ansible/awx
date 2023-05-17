import getRouteConfig from './routeConfig';
jest.mock('util/webWorker', () => jest.fn());

const userProfile = {
  isSuperUser: false,
  isSystemAuditor: false,
  isOrgAdmin: false,
  isNotificationAdmin: false,
  isExecEnvAdmin: false,
  systemConfig: { SUBSCRIPTION_USAGE_MODEL: 'unique_managed_hosts' },
};

const filterPaths = (sidebar) => {
  const visibleRoutes = [];
  sidebar.forEach(({ routes }) => {
    routes.forEach((route) => {
      visibleRoutes.push(route.path);
    });
  });

  return visibleRoutes;
};
describe('getRouteConfig', () => {
  test('routes for system admin', () => {
    const sidebar = getRouteConfig({ ...userProfile, isSuperUser: true });
    const filteredPaths = filterPaths(sidebar);
    expect(filteredPaths).toEqual([
      '/home',
      '/jobs',
      '/schedules',
      '/activity_stream',
      '/workflow_approvals',
      '/host_metrics',
      '/templates',
      '/credentials',
      '/projects',
      '/inventories',
      '/hosts',
      '/organizations',
      '/users',
      '/teams',
      '/credential_types',
      '/notification_templates',
      '/management_jobs',
      '/instance_groups',
      '/instances',
      '/applications',
      '/execution_environments',
      '/topology_view',
      '/settings',
    ]);
  });

  test('routes for system auditor', () => {
    const sidebar = getRouteConfig({ ...userProfile, isSystemAuditor: true });
    const filteredPaths = filterPaths(sidebar);
    expect(filteredPaths).toEqual([
      '/home',
      '/jobs',
      '/schedules',
      '/activity_stream',
      '/workflow_approvals',
      '/host_metrics',
      '/templates',
      '/credentials',
      '/projects',
      '/inventories',
      '/hosts',
      '/organizations',
      '/users',
      '/teams',
      '/credential_types',
      '/notification_templates',
      '/management_jobs',
      '/instance_groups',
      '/instances',
      '/applications',
      '/execution_environments',
      '/topology_view',
      '/settings',
    ]);
  });

  test('routes for org admin', () => {
    const sidebar = getRouteConfig({ ...userProfile, isOrgAdmin: true });
    const filteredPaths = filterPaths(sidebar);
    expect(filteredPaths).toEqual([
      '/home',
      '/jobs',
      '/schedules',
      '/activity_stream',
      '/workflow_approvals',
      '/templates',
      '/credentials',
      '/projects',
      '/inventories',
      '/hosts',
      '/organizations',
      '/users',
      '/teams',
      '/credential_types',
      '/notification_templates',
      '/instance_groups',
      '/applications',
      '/execution_environments',
    ]);
  });

  test('routes for notifications admin', () => {
    const sidebar = getRouteConfig({
      ...userProfile,
      isNotificationAdmin: true,
    });
    const filteredPaths = filterPaths(sidebar);
    expect(filteredPaths).toEqual([
      '/home',
      '/jobs',
      '/schedules',
      '/activity_stream',
      '/workflow_approvals',
      '/templates',
      '/credentials',
      '/projects',
      '/inventories',
      '/hosts',
      '/organizations',
      '/users',
      '/teams',
      '/credential_types',
      '/notification_templates',
      '/instance_groups',
      '/applications',
      '/execution_environments',
    ]);
  });

  test('routes for execution environments admin', () => {
    const sidebar = getRouteConfig({ ...userProfile, isExecEnvAdmin: true });
    const filteredPaths = filterPaths(sidebar);
    expect(filteredPaths).toEqual([
      '/home',
      '/jobs',
      '/schedules',
      '/activity_stream',
      '/workflow_approvals',
      '/templates',
      '/credentials',
      '/projects',
      '/inventories',
      '/hosts',
      '/organizations',
      '/users',
      '/teams',
      '/credential_types',
      '/instance_groups',
      '/applications',
      '/execution_environments',
    ]);
  });

  test('routes for regular users', () => {
    const sidebar = getRouteConfig(userProfile);
    const filteredPaths = filterPaths(sidebar);
    expect(filteredPaths).toEqual([
      '/home',
      '/jobs',
      '/schedules',
      '/activity_stream',
      '/workflow_approvals',
      '/templates',
      '/credentials',
      '/projects',
      '/inventories',
      '/hosts',
      '/organizations',
      '/users',
      '/teams',
      '/credential_types',
      '/instance_groups',
      '/applications',
      '/execution_environments',
    ]);
  });

  test('routes for execution environment admins and notification admin', () => {
    const sidebar = getRouteConfig({
      ...userProfile,
      isExecEnvAdmin: true,
      isNotificationAdmin: true,
    });
    const filteredPaths = filterPaths(sidebar);
    expect(filteredPaths).toEqual([
      '/home',
      '/jobs',
      '/schedules',
      '/activity_stream',
      '/workflow_approvals',
      '/templates',
      '/credentials',
      '/projects',
      '/inventories',
      '/hosts',
      '/organizations',
      '/users',
      '/teams',
      '/credential_types',
      '/notification_templates',
      '/instance_groups',
      '/applications',
      '/execution_environments',
    ]);
  });

  test('routes for execution environment admins and organization admins', () => {
    const sidebar = getRouteConfig({
      ...userProfile,
      isExecEnvAdmin: true,
      isOrgAdmin: true,
    });
    const filteredPaths = filterPaths(sidebar);
    expect(filteredPaths).toEqual([
      '/home',
      '/jobs',
      '/schedules',
      '/activity_stream',
      '/workflow_approvals',
      '/templates',
      '/credentials',
      '/projects',
      '/inventories',
      '/hosts',
      '/organizations',
      '/users',
      '/teams',
      '/credential_types',
      '/notification_templates',
      '/instance_groups',
      '/applications',
      '/execution_environments',
    ]);
  });

  test('routes for notification admins and organization admins', () => {
    const sidebar = getRouteConfig({
      ...userProfile,
      isNotificationAdmin: true,
      isOrgAdmin: true,
    });
    const filteredPaths = filterPaths(sidebar);
    expect(filteredPaths).toEqual([
      '/home',
      '/jobs',
      '/schedules',
      '/activity_stream',
      '/workflow_approvals',
      '/templates',
      '/credentials',
      '/projects',
      '/inventories',
      '/hosts',
      '/organizations',
      '/users',
      '/teams',
      '/credential_types',
      '/notification_templates',
      '/instance_groups',
      '/applications',
      '/execution_environments',
    ]);
  });
});
