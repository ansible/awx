import Base from '../Base';

class Config extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/config/';
    this.read = this.read.bind(this);
  }
}

export default Config;
