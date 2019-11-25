import Base from '../Base';
import InstanceGroupsMixin from '../mixins/InstanceGroups.mixin';

class Inventories extends InstanceGroupsMixin(Base) {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/inventories/';

    this.readAccessList = this.readAccessList.bind(this);
  }

  readAccessList(id, params) {
    return this.http.get(`${this.baseUrl}${id}/access_list/`, {
      params,
    });
  }

  readHosts(id, params) {
    return this.http.get(`${this.baseUrl}${id}/hosts/`, { params });
  }
}

export default Inventories;
