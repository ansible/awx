import Root from './Root';

describe('RootAPI', () => {
  const createPromise = () => Promise.resolve();
  const mockHttp = {
    get: jest.fn(createPromise),
    post: jest.fn(createPromise),
  };

  const RootAPI = new Root(mockHttp);

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('login calls get and post with expected content headers', async done => {
    const headers = { 'Content-Type': 'application/x-www-form-urlencoded' };

    await RootAPI.login('username', 'password');

    expect(mockHttp.get).toHaveBeenCalledTimes(1);
    expect(mockHttp.get.mock.calls[0]).toContainEqual({ headers });

    expect(mockHttp.post).toHaveBeenCalledTimes(1);
    expect(mockHttp.post.mock.calls[0]).toContainEqual({ headers });

    done();
  });

  test('login sends expected data', async done => {
    await RootAPI.login('foo', 'bar');
    await RootAPI.login('foo', 'bar', 'baz');

    expect(mockHttp.post).toHaveBeenCalledTimes(2);
    expect(mockHttp.post.mock.calls[0]).toContainEqual(
      'username=foo&password=bar&next=%2Fapi%2Fv2%2Fconfig%2F'
    );
    expect(mockHttp.post.mock.calls[1]).toContainEqual(
      'username=foo&password=bar&next=baz'
    );

    done();
  });

  test('logout calls expected http method', async done => {
    await RootAPI.logout();

    expect(mockHttp.get).toHaveBeenCalledTimes(1);

    done();
  });
});
