import Base from '../Base';

class Credentials extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/credentials/';
  }
}

export default Credentials;
