import { describeNotificationMixin } from '../../../testUtils/apiReusable';
import Organizations from './Organizations';

describe('OrganizationsAPI', () => {
  const orgId = 1;
  let mockHttp;
  let OrganizationsAPI;
  beforeEach(() => {
    const createPromise = () => Promise.resolve();
    mockHttp = { get: jest.fn(createPromise) };

    OrganizationsAPI = new Organizations(mockHttp);
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  test('read access list calls get with expected params', async () => {
    const testParams = { foo: 'bar' };
    const testParamsDuplicates = { foo: ['bar', 'baz'] };

    const mockBaseURL = `api/v2/organizations/${orgId}/access_list/`;

    await OrganizationsAPI.readAccessList(orgId);
    await OrganizationsAPI.readAccessList(orgId, testParams);
    await OrganizationsAPI.readAccessList(orgId, testParamsDuplicates);

    expect(mockHttp.get).toHaveBeenCalledTimes(3);
    expect(mockHttp.get.mock.calls[0][0]).toEqual(`${mockBaseURL}`);
    expect(mockHttp.get.mock.calls[0][1]).toEqual({ params: undefined });
    expect(mockHttp.get.mock.calls[1][0]).toEqual(`${mockBaseURL}`);
    expect(mockHttp.get.mock.calls[1][1]).toEqual({ params: { foo: 'bar' } });
    expect(mockHttp.get.mock.calls[2][0]).toEqual(`${mockBaseURL}`);
    expect(mockHttp.get.mock.calls[2][1]).toEqual({
      params: { foo: ['bar', 'baz'] },
    });
  });

  test('read teams calls get with expected params', async () => {
    const testParams = { foo: 'bar' };
    const testParamsDuplicates = { foo: ['bar', 'baz'] };

    const mockBaseURL = `api/v2/organizations/${orgId}/teams/`;

    await OrganizationsAPI.readTeams(orgId);
    await OrganizationsAPI.readTeams(orgId, testParams);
    await OrganizationsAPI.readTeams(orgId, testParamsDuplicates);

    expect(mockHttp.get).toHaveBeenCalledTimes(3);
    expect(mockHttp.get.mock.calls[0][0]).toEqual(`${mockBaseURL}`);
    expect(mockHttp.get.mock.calls[0][1]).toEqual({ params: undefined });
    expect(mockHttp.get.mock.calls[1][0]).toEqual(`${mockBaseURL}`);
    expect(mockHttp.get.mock.calls[1][1]).toEqual({ params: { foo: 'bar' } });
    expect(mockHttp.get.mock.calls[2][0]).toEqual(`${mockBaseURL}`);
    expect(mockHttp.get.mock.calls[2][1]).toEqual({
      params: { foo: ['bar', 'baz'] },
    });
  });
});

describeNotificationMixin(Organizations, 'Organizations[NotificationsMixin]');
