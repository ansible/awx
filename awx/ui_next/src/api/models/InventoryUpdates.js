import Base from '../Base';
import LaunchUpdateMixin from '../mixins/LaunchUpdate.mixin';

class InventoryUpdates extends LaunchUpdateMixin(Base) {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/inventory_updates/';
    this.allowSyncCancel = this.allowSyncCancel.bind(this);
    this.cancelSyncSource = this.cancelSyncSource.bind(this);
  }

  allowSyncCancel(sourceId) {
    return this.http.get(`${this.baseUrl}${sourceId}/cancel/`);
  }

  cancelSyncSource(sourceId) {
    return this.http.post(`${this.baseUrl}${sourceId}/cancel/`);
  }
}
export default InventoryUpdates;
