import Base from '../Base';

class Tokens extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/tokens/';
  }
}

export default Tokens;
