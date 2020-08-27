import Base from '../Base';

class Credentials extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/credentials/';

    this.readAccessList = this.readAccessList.bind(this);
    this.readAccessOptions = this.readAccessOptions.bind(this);
    this.readInputSources = this.readInputSources.bind(this);
  }

  readAccessList(id, params) {
    return this.http.get(`${this.baseUrl}${id}/access_list/`, {
      params,
    });
  }

  readAccessOptions(id) {
    return this.http.options(`${this.baseUrl}${id}/access_list/`);
  }

  readInputSources(id, params) {
    return this.http.get(`${this.baseUrl}${id}/input_sources/`, {
      params,
    });
  }
}

export default Credentials;
