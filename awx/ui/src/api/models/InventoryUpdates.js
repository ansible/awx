import Base from '../Base';
import RunnableMixin from '../mixins/Runnable.mixin';

class InventoryUpdates extends RunnableMixin(Base) {
  constructor(http) {
    super(http);
    this.baseUrl = 'api/v2/inventory_updates/';
    this.createSyncCancel = this.createSyncCancel.bind(this);
  }

  createSyncCancel(sourceId) {
    return this.http.post(`${this.baseUrl}${sourceId}/cancel/`);
  }

  readCredentials(id) {
    return this.http.get(`${this.baseUrl}${id}/credentials/`);
  }
}
export default InventoryUpdates;
