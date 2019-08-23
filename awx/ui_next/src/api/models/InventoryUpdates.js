import Base from '../Base';

class InventoryUpdates extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/inventory_updates/';
  }
}

export default InventoryUpdates;
