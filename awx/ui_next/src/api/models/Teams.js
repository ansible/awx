import Base from '../Base';

class Teams extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/teams/';
  }

  associateRole(teamId, roleId) {
    return this.http.post(`${this.baseUrl}${teamId}/roles/`, { id: roleId });
  }

  disassociateRole(teamId, roleId) {
    return this.http.post(`${this.baseUrl}${teamId}/roles/`, {
      id: roleId,
      disassociate: true,
    });
  }
}

export default Teams;
