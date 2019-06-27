import Organizations from './Organizations';
import { describeNotificationMixin } from '../../../testUtils/apiReusable';

describe('OrganizationsAPI', () => {
  const orgId = 1;
  const searchParams = { foo: 'bar' };
  const createPromise = () => Promise.resolve();
  const mockHttp = ({ get: jest.fn(createPromise) });

  const OrganizationsAPI = new Organizations(mockHttp);

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('read access list calls get with expected params', async (done) => {
    await OrganizationsAPI.readAccessList(orgId);
    await OrganizationsAPI.readAccessList(orgId, searchParams);

    expect(mockHttp.get).toHaveBeenCalledTimes(2);
    expect(mockHttp.get.mock.calls[0]).toContainEqual(`/api/v2/organizations/${orgId}/access_list/`, { params: {} });
    expect(mockHttp.get.mock.calls[1]).toContainEqual(`/api/v2/organizations/${orgId}/access_list/`, { params: searchParams });

    done();
  });

  test('read teams calls get with expected params', async (done) => {
    await OrganizationsAPI.readTeams(orgId);
    await OrganizationsAPI.readTeams(orgId, searchParams);

    expect(mockHttp.get).toHaveBeenCalledTimes(2);
    expect(mockHttp.get.mock.calls[0]).toContainEqual(`/api/v2/organizations/${orgId}/teams/`, { params: {} });
    expect(mockHttp.get.mock.calls[1]).toContainEqual(`/api/v2/organizations/${orgId}/teams/`, { params: searchParams });

    done();
  });
});

describeNotificationMixin(Organizations, 'Organizations[NotificationsMixin]');
