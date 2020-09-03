import Base from '../Base';

class InventoryScripts extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/inventory_scripts/';
  }
}

export default InventoryScripts;
