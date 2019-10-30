import Base from '../Base';

class Hosts extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/hosts/';
  }
}

export default Hosts;
