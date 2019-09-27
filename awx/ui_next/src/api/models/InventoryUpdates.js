import Base from '../Base';
import LaunchUpdateMixin from '../mixins/LaunchUpdate.mixin';

class InventoryUpdates extends LaunchUpdateMixin(Base) {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/inventory_updates/';
  }
}

export default InventoryUpdates;
