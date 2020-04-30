import Base from '../Base';
import LaunchUpdateMixin from '../mixins/LaunchUpdate.mixin';

class InventoryUpdates extends LaunchUpdateMixin(Base) {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/inventory_updates/';
    this.createSyncCancel = this.createSyncCancel.bind(this);
  }

  createSyncCancel(sourceId) {
    return this.http.post(`${this.baseUrl}${sourceId}/cancel/`);
  }
}
export default InventoryUpdates;
