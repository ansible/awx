import Base from '../Base';

class Roles extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/roles/';
  }

  disassociateUserRole(roleId, userId) {
    return this.http.post(`${this.baseUrl}${roleId}/users/`, {
      disassociate: true,
      id: userId,
    });
  }

  disassociateTeamRole(roleId, teamId) {
    return this.http.post(`${this.baseUrl}${roleId}/teams/`, {
      disassociate: true,
      id: teamId,
    });
  }
}
export default Roles;
