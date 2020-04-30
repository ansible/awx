import Base from '../Base';
import LaunchUpdateMixin from '../mixins/LaunchUpdate.mixin';

class InventorySources extends LaunchUpdateMixin(Base) {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/inventory_sources/';

    this.allowSyncStart = this.allowSyncStart.bind(this);
    this.startSyncSource = this.startSyncSource.bind(this);
  }

  allowSyncStart(sourceId) {
    return this.http.get(`${this.baseUrl}${sourceId}/update/`);
  }

  startSyncSource(sourceId, extraVars) {
    return this.http.post(`${this.baseUrl}${sourceId}/update/`, {
      extra_vars: extraVars,
    });
  }
}
export default InventorySources;
