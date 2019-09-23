import Base from '../Base';

class Inventories extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/inventories/';
  }
}

export default Inventories;
