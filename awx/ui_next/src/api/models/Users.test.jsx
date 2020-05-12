import Users from './Users';

describe('UsersAPI', () => {
  const userId = 1;
  const roleId = 7;
  const createPromise = () => Promise.resolve();
  const mockHttp = { post: jest.fn(createPromise) };

  const UsersAPI = new Users(mockHttp);

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('associate role calls post with expected params', async done => {
    await UsersAPI.associateRole(userId, roleId);

    expect(mockHttp.post).toHaveBeenCalledTimes(1);
    expect(
      mockHttp.post.mock.calls[0]
    ).toContainEqual(`/api/v2/users/${userId}/roles/`, { id: roleId });

    done();
  });

  test('read users calls post with expected params', async done => {
    await UsersAPI.disassociateRole(userId, roleId);

    expect(mockHttp.post).toHaveBeenCalledTimes(1);
    expect(mockHttp.post.mock.calls[0]).toContainEqual(
      `/api/v2/users/${userId}/roles/`,
      {
        id: roleId,
        disassociate: true,
      }
    );

    done();
  });
});
