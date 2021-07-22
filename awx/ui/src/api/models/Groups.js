import Base from '../Base';

class Groups extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/groups/';

    this.associateHost = this.associateHost.bind(this);
    this.createHost = this.createHost.bind(this);
    this.readAllHosts = this.readAllHosts.bind(this);
    this.disassociateHost = this.disassociateHost.bind(this);
  }

  associateHost(id, hostId) {
    return this.http.post(`${this.baseUrl}${id}/hosts/`, {
      id: hostId,
    });
  }

  createHost(id, data) {
    return this.http.post(`${this.baseUrl}${id}/hosts/`, data);
  }

  readAllHosts(id, params) {
    return this.http.get(`${this.baseUrl}${id}/all_hosts/`, {
      params,
    });
  }

  disassociateHost(id, host) {
    return this.http.post(`${this.baseUrl}${id}/hosts/`, {
      id: host.id,
      disassociate: true,
    });
  }

  readChildren(id, params) {
    return this.http.get(`${this.baseUrl}${id}/children/`, { params });
  }

  associateChildGroup(id, childId) {
    return this.http.post(`${this.baseUrl}${id}/children/`, { id: childId });
  }

  disassociateChildGroup(id, childId) {
    return this.http.post(`${this.baseUrl}${id}/children/`, {
      disassociate: id,
      id: childId,
    });
  }

  readPotentialGroups(id, params) {
    return this.http.get(`${this.baseUrl}${id}/potential_children/`, {
      params,
    });
  }
}

export default Groups;
