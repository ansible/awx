import Base from '../Base';

class Hosts extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/hosts/';

    this.readFacts = this.readFacts.bind(this);
    this.readGroups = this.readGroups.bind(this);
    this.readGroupsOptions = this.readGroupsOptions.bind(this);
  }

  readFacts(id) {
    return this.http.get(`${this.baseUrl}${id}/ansible_facts/`);
  }

  readGroups(id, params) {
    return this.http.get(`${this.baseUrl}${id}/groups/`, { params });
  }

  readGroupsOptions(id) {
    return this.http.options(`${this.baseUrl}${id}/groups/`);
  }
}

export default Hosts;
