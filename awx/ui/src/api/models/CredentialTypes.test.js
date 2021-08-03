import CredentialTypes from './CredentialTypes';

const typesData = [
  { id: 1, kind: 'machine' },
  { id: 2, kind: 'cloud' },
];

describe('CredentialTypesAPI', () => {
  test('should load all types', async () => {
    const getPromise = () =>
      Promise.resolve({
        data: {
          results: typesData,
        },
      });
    const mockHttp = { get: jest.fn(getPromise) };
    const CredentialTypesAPI = new CredentialTypes(mockHttp);

    const types = await CredentialTypesAPI.loadAllTypes();

    expect(mockHttp.get).toHaveBeenCalledTimes(1);
    expect(mockHttp.get.mock.calls[0]).toEqual([
      `/api/v2/credential_types/`,
      { params: { page_size: 200 } },
    ]);
    expect(types).toEqual(typesData);
  });

  test('should load all types (2 pages)', async () => {
    const getPromise = () =>
      Promise.resolve({
        data: {
          results: typesData,
          next: 2,
        },
      });
    const mockHttp = { get: jest.fn(getPromise) };
    const CredentialTypesAPI = new CredentialTypes(mockHttp);

    const types = await CredentialTypesAPI.loadAllTypes();

    expect(mockHttp.get).toHaveBeenCalledTimes(2);
    expect(mockHttp.get.mock.calls[0]).toEqual([
      `/api/v2/credential_types/`,
      { params: { page_size: 200 } },
    ]);
    expect(mockHttp.get.mock.calls[1]).toEqual([
      `/api/v2/credential_types/`,
      { params: { page_size: 200, page: 2 } },
    ]);
    expect(types).toHaveLength(4);
  });

  test('should filter by acceptable kinds', async () => {
    const getPromise = () =>
      Promise.resolve({
        data: {
          results: typesData,
        },
      });
    const mockHttp = { get: jest.fn(getPromise) };
    const CredentialTypesAPI = new CredentialTypes(mockHttp);

    const types = await CredentialTypesAPI.loadAllTypes(['machine']);

    expect(types).toEqual([typesData[0]]);
  });
});
