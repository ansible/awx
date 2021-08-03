import Base from '../Base';

class Teams extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/teams/';
  }

  associateRole(teamId, roleId) {
    return this.http.post(`${this.baseUrl}${teamId}/roles/`, {
      id: roleId,
    });
  }

  disassociateRole(teamId, roleId) {
    return this.http.post(`${this.baseUrl}${teamId}/roles/`, {
      id: roleId,
      disassociate: true,
    });
  }

  readRoles(teamId, params) {
    return this.http.get(`${this.baseUrl}${teamId}/roles/`, {
      params,
    });
  }

  readRoleOptions(teamId) {
    return this.http.options(`${this.baseUrl}${teamId}/roles/`);
  }

  readAccessList(teamId, params) {
    return this.http.get(`${this.baseUrl}${teamId}/access_list/`, {
      params,
    });
  }

  readAccessOptions(id) {
    return this.http.options(`${this.baseUrl}${id}/access_list/`);
  }

  readUsersAccessOptions(teamId) {
    return this.http.options(`${this.baseUrl}${teamId}/users/`);
  }
}

export default Teams;
