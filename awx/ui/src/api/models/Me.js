import Base from '../Base';

class Me extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/me/';
  }
}

export default Me;
