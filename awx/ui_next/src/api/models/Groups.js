import Base from '../Base';

class Groups extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/groups/';

    this.readAllHosts = this.readAllHosts.bind(this);
  }

  readAllHosts(id, params) {
    return this.http.get(`${this.baseUrl}${id}/all_hosts/`, { params });
  }
}

export default Groups;
