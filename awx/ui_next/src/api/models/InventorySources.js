import Base from '../Base';
import LaunchUpdateMixin from '../mixins/LaunchUpdate.mixin';

class InventorySources extends LaunchUpdateMixin(Base) {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/inventory_sources/';

    this.createSyncStart = this.createSyncStart.bind(this);
  }

  createSyncStart(sourceId, extraVars) {
    return this.http.post(`${this.baseUrl}${sourceId}/update/`, {
      extra_vars: extraVars,
    });
  }
}
export default InventorySources;
