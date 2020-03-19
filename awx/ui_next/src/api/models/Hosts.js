import Base from '../Base';

class Hosts extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/hosts/';
  }

  readFacts(id) {
    return this.http.get(`${this.baseUrl}${id}/ansible_facts/`);
  }
}

export default Hosts;
