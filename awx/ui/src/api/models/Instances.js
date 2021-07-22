import Base from '../Base';

class Instances extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/instances/';
  }
}

export default Instances;
