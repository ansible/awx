import Base from './Base';

describe('Base', () => {
  const mockBaseURL = '/api/v2/organizations/';

  let BaseAPI;
  let mockHttp;

  beforeEach(() => {
    const createPromise = () => Promise.resolve();
    mockHttp = {
      delete: jest.fn(createPromise),
      get: jest.fn(createPromise),
      options: jest.fn(createPromise),
      patch: jest.fn(createPromise),
      post: jest.fn(createPromise),
      put: jest.fn(createPromise),
    };
    BaseAPI = new Base(mockHttp, mockBaseURL);
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  test('create calls http method with expected data', async () => {
    const data = { name: 'test ' };
    await BaseAPI.create(data);

    expect(mockHttp.post).toHaveBeenCalledTimes(1);
    expect(mockHttp.post.mock.calls[0][1]).toEqual(data);
  });

  test('destroy calls http method with expected data', async () => {
    const resourceId = 1;
    await BaseAPI.destroy(resourceId);

    expect(mockHttp.delete).toHaveBeenCalledTimes(1);
    expect(mockHttp.delete.mock.calls[0][0]).toEqual(
      `${mockBaseURL}${resourceId}/`
    );
  });

  test('read calls http method with expected data', async () => {
    const testParams = { foo: 'bar' };
    const testParamsDuplicates = { foo: ['bar', 'baz'] };

    await BaseAPI.read(testParams);
    await BaseAPI.read();
    await BaseAPI.read(testParamsDuplicates);

    expect(mockHttp.get).toHaveBeenCalledTimes(3);
    expect(mockHttp.get.mock.calls[0][0]).toEqual(`${mockBaseURL}`);
    expect(mockHttp.get.mock.calls[0][1]).toEqual({ params: { foo: 'bar' } });
    expect(mockHttp.get.mock.calls[1][0]).toEqual(`${mockBaseURL}`);
    expect(mockHttp.get.mock.calls[1][1]).toEqual({ params: undefined });
    expect(mockHttp.get.mock.calls[2][0]).toEqual(`${mockBaseURL}`);
    expect(mockHttp.get.mock.calls[2][1]).toEqual({
      params: { foo: ['bar', 'baz'] },
    });
  });

  test('readDetail calls http method with expected data', async () => {
    const resourceId = 1;

    await BaseAPI.readDetail(resourceId);

    expect(mockHttp.get).toHaveBeenCalledTimes(1);
    expect(mockHttp.get.mock.calls[0][0]).toEqual(
      `${mockBaseURL}${resourceId}/`
    );
  });

  test('readOptions calls http method with expected data', async () => {
    await BaseAPI.readOptions();

    expect(mockHttp.options).toHaveBeenCalledTimes(1);
    expect(mockHttp.options.mock.calls[0][0]).toEqual(`${mockBaseURL}`);
  });

  test('replace calls http method with expected data', async () => {
    const resourceId = 1;
    const data = { name: 'test ' };

    await BaseAPI.replace(resourceId, data);

    expect(mockHttp.put).toHaveBeenCalledTimes(1);
    expect(mockHttp.put.mock.calls[0][0]).toEqual(
      `${mockBaseURL}${resourceId}/`
    );
    expect(mockHttp.put.mock.calls[0][1]).toEqual(data);
  });

  test('update calls http method with expected data', async () => {
    const resourceId = 1;
    const data = { name: 'test ' };

    await BaseAPI.update(resourceId, data);

    expect(mockHttp.patch).toHaveBeenCalledTimes(1);
    expect(mockHttp.patch.mock.calls[0][0]).toEqual(
      `${mockBaseURL}${resourceId}/`
    );
    expect(mockHttp.patch.mock.calls[0][1]).toEqual(data);
  });
});
