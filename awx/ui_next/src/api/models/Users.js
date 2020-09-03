import Base from '../Base';

class Users extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/users/';
  }

  associateRole(userId, roleId) {
    return this.http.post(`${this.baseUrl}${userId}/roles/`, {
      id: roleId,
    });
  }

  createToken(userId, data) {
    return this.http.post(`${this.baseUrl}${userId}/authorized_tokens/`, data);
  }

  disassociateRole(userId, roleId) {
    return this.http.post(`${this.baseUrl}${userId}/roles/`, {
      id: roleId,
      disassociate: true,
    });
  }

  readOrganizations(userId, params) {
    return this.http.get(`${this.baseUrl}${userId}/organizations/`, {
      params,
    });
  }

  readRoles(userId, params) {
    return this.http.get(`${this.baseUrl}${userId}/roles/`, {
      params,
    });
  }

  readRoleOptions(userId) {
    return this.http.options(`${this.baseUrl}${userId}/roles/`);
  }

  readTeams(userId, params) {
    return this.http.get(`${this.baseUrl}${userId}/teams/`, {
      params,
    });
  }

  readTeamsOptions(userId) {
    return this.http.options(`${this.baseUrl}${userId}/teams/`);
  }

  readTokens(userId, params) {
    return this.http.get(`${this.baseUrl}${userId}/tokens/`, {
      params,
    });
  }

  readAdminOfOrganizations(userId, params) {
    return this.http.get(`${this.baseUrl}${userId}/admin_of_organizations/`, {
      params,
    });
  }

  readTokenOptions(userId) {
    return this.http.options(`${this.baseUrl}${userId}/tokens/`);
  }
}

export default Users;
