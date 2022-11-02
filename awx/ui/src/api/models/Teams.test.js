import Teams from './Teams';

describe('TeamsAPI', () => {
  const teamId = 1;
  const roleId = 7;

  let TeamsAPI;
  let mockHttp;

  beforeEach(() => {
    const createPromise = () => Promise.resolve();
    mockHttp = { post: jest.fn(createPromise) };

    TeamsAPI = new Teams(mockHttp);
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  test('associate role calls post with expected params', async () => {
    await TeamsAPI.associateRole(teamId, roleId);

    expect(mockHttp.post).toHaveBeenCalledTimes(1);
    expect(mockHttp.post.mock.calls[0]).toContainEqual(
      `api/v2/teams/${teamId}/roles/`,
      { id: roleId }
    );
  });

  test('read teams calls post with expected params', async () => {
    await TeamsAPI.disassociateRole(teamId, roleId);

    expect(mockHttp.post).toHaveBeenCalledTimes(1);
    expect(mockHttp.post.mock.calls[0]).toContainEqual(
      `api/v2/teams/${teamId}/roles/`,
      {
        id: roleId,
        disassociate: true,
      }
    );
  });
});
