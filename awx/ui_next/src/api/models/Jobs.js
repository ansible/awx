import Base from '../Base';

class Jobs extends Base {
  constructor (http) {
    super(http);
    this.baseUrl = '/api/v2/jobs/';
  }
}

export default Jobs;
