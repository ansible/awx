import Base from '../Base';

class Groups extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/groups/';
  }
}

export default Groups;
