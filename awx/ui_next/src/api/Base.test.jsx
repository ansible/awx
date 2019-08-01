import Base from './Base';

describe('Base', () => {
  const createPromise = () => Promise.resolve();
  const mockBaseURL = '/api/v2/organizations/';
  const mockHttp = {
    delete: jest.fn(createPromise),
    get: jest.fn(createPromise),
    options: jest.fn(createPromise),
    patch: jest.fn(createPromise),
    post: jest.fn(createPromise),
    put: jest.fn(createPromise),
  };

  const BaseAPI = new Base(mockHttp, mockBaseURL);

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('create calls http method with expected data', async done => {
    const data = { name: 'test ' };
    await BaseAPI.create(data);

    expect(mockHttp.post).toHaveBeenCalledTimes(1);
    expect(mockHttp.post.mock.calls[0][1]).toEqual(data);

    done();
  });

  test('destroy calls http method with expected data', async done => {
    const resourceId = 1;
    await BaseAPI.destroy(resourceId);

    expect(mockHttp.delete).toHaveBeenCalledTimes(1);
    expect(mockHttp.delete.mock.calls[0][0]).toEqual(
      `${mockBaseURL}${resourceId}/`
    );

    done();
  });

  test('read calls http method with expected data', async done => {
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
    done();
  });

  test('readDetail calls http method with expected data', async done => {
    const resourceId = 1;

    await BaseAPI.readDetail(resourceId);

    expect(mockHttp.get).toHaveBeenCalledTimes(1);
    expect(mockHttp.get.mock.calls[0][0]).toEqual(
      `${mockBaseURL}${resourceId}/`
    );
    done();
  });

  test('readOptions calls http method with expected data', async done => {
    await BaseAPI.readOptions();

    expect(mockHttp.options).toHaveBeenCalledTimes(1);
    expect(mockHttp.options.mock.calls[0][0]).toEqual(`${mockBaseURL}`);
    done();
  });

  test('replace calls http method with expected data', async done => {
    const resourceId = 1;
    const data = { name: 'test ' };

    await BaseAPI.replace(resourceId, data);

    expect(mockHttp.put).toHaveBeenCalledTimes(1);
    expect(mockHttp.put.mock.calls[0][0]).toEqual(
      `${mockBaseURL}${resourceId}/`
    );
    expect(mockHttp.put.mock.calls[0][1]).toEqual(data);

    done();
  });

  test('update calls http method with expected data', async done => {
    const resourceId = 1;
    const data = { name: 'test ' };

    await BaseAPI.update(resourceId, data);

    expect(mockHttp.patch).toHaveBeenCalledTimes(1);
    expect(mockHttp.patch.mock.calls[0][0]).toEqual(
      `${mockBaseURL}${resourceId}/`
    );
    expect(mockHttp.patch.mock.calls[0][1]).toEqual(data);

    done();
  });
});
