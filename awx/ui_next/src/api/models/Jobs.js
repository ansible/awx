import Base from '../Base';

class Jobs extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/jobs/';
  }

  readDetail (id, type) {
    // TODO: adjust url based on type
    return this.http.get(`${this.baseUrl}${id}/`);
  }
}

export default Jobs;
