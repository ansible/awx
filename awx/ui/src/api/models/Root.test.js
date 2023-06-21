import Root from './Root';

describe('RootAPI', () => {
  let mockHttp;
  let RootAPI;
  beforeEach(() => {
    const createPromise = () => Promise.resolve();
    mockHttp = {
      get: jest.fn(createPromise),
      post: jest.fn(createPromise),
    };

    RootAPI = new Root(mockHttp);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('login calls get and post with expected content headers', async () => {
    const headers = { 'Content-Type': 'application/x-www-form-urlencoded' };

    await RootAPI.login('username', 'password');

    expect(mockHttp.get).toHaveBeenCalledTimes(1);
    expect(mockHttp.get.mock.calls[0]).toContainEqual({ headers });

    expect(mockHttp.post).toHaveBeenCalledTimes(1);
    expect(mockHttp.post.mock.calls[0]).toContainEqual({ headers });
  });

  test('login sends expected data', async () => {
    await RootAPI.login('foo', 'bar');
    await RootAPI.login('foo', 'bar', 'baz');

    expect(mockHttp.post).toHaveBeenCalledTimes(2);
    expect(mockHttp.post.mock.calls[0]).toContainEqual(
      'username=foo&password=bar&next=api%2Fv2%2Fconfig%2F'
    );
    expect(mockHttp.post.mock.calls[1]).toContainEqual(
      'username=foo&password=bar&next=baz'
    );
  });

  test('logout calls expected http method', async () => {
    await RootAPI.logout();

    expect(mockHttp.get).toHaveBeenCalledTimes(1);
  });
});
