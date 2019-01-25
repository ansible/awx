import APIClient from '../src/api';

const invalidCookie = 'invalid';
const validLoggedOutCookie = 'current_user=%7B%22id%22%3A1%2C%22type%22%3A%22user%22%2C%22url%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2F%22%2C%22related%22%3A%7B%22admin_of_organizations%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Fadmin_of_organizations%2F%22%2C%22authorized_tokens%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Fauthorized_tokens%2F%22%2C%22roles%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Froles%2F%22%2C%22organizations%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Forganizations%2F%22%2C%22access_list%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Faccess_list%2F%22%2C%22teams%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Fteams%2F%22%2C%22tokens%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Ftokens%2F%22%2C%22personal_tokens%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Fpersonal_tokens%2F%22%2C%22credentials%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Fcredentials%2F%22%2C%22activity_stream%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Factivity_stream%2F%22%2C%22projects%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Fprojects%2F%22%7D%2C%22summary_fields%22%3A%7B%7D%2C%22created%22%3A%222018-10-19T16%3A30%3A59.141963Z%22%2C%22username%22%3A%22admin%22%2C%22first_name%22%3A%22%22%2C%22last_name%22%3A%22%22%2C%22email%22%3A%22%22%2C%22is_superuser%22%3Atrue%2C%22is_system_auditor%22%3Afalse%2C%22ldap_dn%22%3A%22%22%2C%22external_account%22%3Anull%2C%22auth%22%3A%5B%5D%7D; userLoggedIn=false; csrftoken=lhOHpLQUFHlIVqx8CCZmEpdEZAz79GIRBIT3asBzTbPE7HS7wizt7WBsgJClz8Ge';
const validLoggedInCookie = 'current_user=%7B%22id%22%3A1%2C%22type%22%3A%22user%22%2C%22url%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2F%22%2C%22related%22%3A%7B%22admin_of_organizations%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Fadmin_of_organizations%2F%22%2C%22authorized_tokens%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Fauthorized_tokens%2F%22%2C%22roles%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Froles%2F%22%2C%22organizations%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Forganizations%2F%22%2C%22access_list%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Faccess_list%2F%22%2C%22teams%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Fteams%2F%22%2C%22tokens%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Ftokens%2F%22%2C%22personal_tokens%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Fpersonal_tokens%2F%22%2C%22credentials%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Fcredentials%2F%22%2C%22activity_stream%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Factivity_stream%2F%22%2C%22projects%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Fprojects%2F%22%7D%2C%22summary_fields%22%3A%7B%7D%2C%22created%22%3A%222018-10-19T16%3A30%3A59.141963Z%22%2C%22username%22%3A%22admin%22%2C%22first_name%22%3A%22%22%2C%22last_name%22%3A%22%22%2C%22email%22%3A%22%22%2C%22is_superuser%22%3Atrue%2C%22is_system_auditor%22%3Afalse%2C%22ldap_dn%22%3A%22%22%2C%22external_account%22%3Anull%2C%22auth%22%3A%5B%5D%7D; userLoggedIn=true; csrftoken=lhOHpLQUFHlIVqx8CCZmEpdEZAz79GIRBIT3asBzTbPE7HS7wizt7WBsgJClz8Ge';

describe('APIClient (api.js)', () => {
  test('isAuthenticated returns false when cookie is invalid', () => {
    APIClient.getCookie = jest.fn(() => invalidCookie);

    const api = new APIClient();
    expect(api.isAuthenticated()).toBe(false);
  });

  test('isAuthenticated returns false when cookie is unauthenticated', () => {
    APIClient.getCookie = jest.fn(() => validLoggedOutCookie);

    const api = new APIClient();
    expect(api.isAuthenticated()).toBe(false);
  });

  test('isAuthenticated returns true when cookie is valid and authenticated', () => {
    APIClient.getCookie = jest.fn(() => validLoggedInCookie);

    const api = new APIClient();
    expect(api.isAuthenticated()).toBe(true);
  });

  test('login calls get and post with expected content headers', async (done) => {
    const headers = { 'Content-Type': 'application/x-www-form-urlencoded' };

    const createPromise = () => Promise.resolve();
    const mockHttp = ({ get: jest.fn(createPromise), post: jest.fn(createPromise) });

    const api = new APIClient(mockHttp);
    await api.login('username', 'password');

    expect(mockHttp.get).toHaveBeenCalledTimes(1);
    expect(mockHttp.get.mock.calls[0]).toContainEqual({ headers });

    expect(mockHttp.post).toHaveBeenCalledTimes(1);
    expect(mockHttp.post.mock.calls[0]).toContainEqual({ headers });

    done();
  });

  test('login sends expected data', async (done) => {
    const createPromise = () => Promise.resolve();
    const mockHttp = ({ get: jest.fn(createPromise), post: jest.fn(createPromise) });

    const api = new APIClient(mockHttp);
    await api.login('foo', 'bar');
    await api.login('foo', 'bar', 'baz');

    expect(mockHttp.post).toHaveBeenCalledTimes(2);
    expect(mockHttp.post.mock.calls[0]).toContainEqual('username=foo&password=bar&next=%2Fapi%2Fv2%2Fconfig%2F');
    expect(mockHttp.post.mock.calls[1]).toContainEqual('username=foo&password=bar&next=baz');

    done();
  });

  test('logout calls expected http method', async (done) => {
    const createPromise = () => Promise.resolve();
    const mockHttp = ({ get: jest.fn(createPromise) });

    const api = new APIClient(mockHttp);
    await api.logout();

    expect(mockHttp.get).toHaveBeenCalledTimes(1);

    done();
  });

  test('getConfig calls expected http method', async (done) => {
    const createPromise = () => Promise.resolve();
    const mockHttp = ({ get: jest.fn(createPromise) });

    const api = new APIClient(mockHttp);
    await api.getConfig();

    expect(mockHttp.get).toHaveBeenCalledTimes(1);

    done();
  });

  test('getOrganizations calls http method with expected data', async (done) => {
    const createPromise = () => Promise.resolve();
    const mockHttp = ({ get: jest.fn(createPromise) });
    const api = new APIClient(mockHttp);

    const defaultParams = {};
    const testParams = { foo: 'bar' };

    await api.getOrganizations(testParams);
    await api.getOrganizations();

    expect(mockHttp.get).toHaveBeenCalledTimes(2);
    expect(mockHttp.get.mock.calls[0][1]).toEqual({ params: testParams });
    expect(mockHttp.get.mock.calls[1][1]).toEqual({ params: defaultParams });
    done();
  });

  test('createOrganization calls http method with expected data', async (done) => {
    const createPromise = () => Promise.resolve();
    const mockHttp = ({ post: jest.fn(createPromise) });

    const api = new APIClient(mockHttp);
    const data = { name: 'test ' };
    await api.createOrganization(data);

    expect(mockHttp.post).toHaveBeenCalledTimes(1);
    expect(mockHttp.post.mock.calls[0][1]).toEqual(data);

    done();
  });

  test('getOrganizationDetails calls http method with expected data', async (done) => {
    const createPromise = () => Promise.resolve();
    const mockHttp = ({ get: jest.fn(createPromise) });

    const api = new APIClient(mockHttp);
    await api.getOrganizationDetails(99);

    expect(mockHttp.get).toHaveBeenCalledTimes(1);
    expect(mockHttp.get.mock.calls[0][0]).toContain('99');

    done();
  });

  test('getInstanceGroups calls expected http method', async (done) => {
    const createPromise = () => Promise.resolve();
    const mockHttp = ({ get: jest.fn(createPromise) });

    const api = new APIClient(mockHttp);
    await api.getInstanceGroups();

    expect(mockHttp.get).toHaveBeenCalledTimes(1);

    done();
  });
});
