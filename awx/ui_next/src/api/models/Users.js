import Base from '../Base';

class Users extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/users/';
  }

  associateRole(userId, roleId) {
    return this.http.post(`${this.baseUrl}${userId}/roles/`, { id: roleId });
  }

  disassociateRole(userId, roleId) {
    return this.http.post(`${this.baseUrl}${userId}/roles/`, {
      id: roleId,
      disassociate: true,
    });
  }
}

export default Users;
