import Base from '../Base';

class Credentials extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/credentials/';

    this.readAccessList = this.readAccessList.bind(this);
    this.readInputSources = this.readInputSources.bind(this);
  }

  readAccessList(id, params) {
    return this.http.get(`${this.baseUrl}${id}/access_list/`, {
      params,
    });
  }

  readInputSources(id, params) {
    return this.http.get(`${this.baseUrl}${id}/input_sources/`, {
      params,
    });
  }
}

export default Credentials;
