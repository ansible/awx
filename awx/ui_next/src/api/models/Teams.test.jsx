import Teams from './Teams';

describe('TeamsAPI', () => {
  const teamId = 1;
  const roleId = 7;
  const createPromise = () => Promise.resolve();
  const mockHttp = { post: jest.fn(createPromise) };

  const TeamsAPI = new Teams(mockHttp);

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('associate role calls post with expected params', async done => {
    await TeamsAPI.associateRole(teamId, roleId);

    expect(mockHttp.post).toHaveBeenCalledTimes(1);
    expect(
      mockHttp.post.mock.calls[0]
    ).toContainEqual(`/api/v2/teams/${teamId}/roles/`, { id: roleId });

    done();
  });

  test('read teams calls post with expected params', async done => {
    await TeamsAPI.disassociateRole(teamId, roleId);

    expect(mockHttp.post).toHaveBeenCalledTimes(1);
    expect(mockHttp.post.mock.calls[0]).toContainEqual(
      `/api/v2/teams/${teamId}/roles/`,
      {
        id: roleId,
        disassociate: true,
      }
    );

    done();
  });
});
