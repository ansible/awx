import Base from '../Base';

class Labels extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/labels/';
  }
}

export default Labels;
