import Base from '../Base';

class Applications extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/applications/';
  }
}

export default Applications;
