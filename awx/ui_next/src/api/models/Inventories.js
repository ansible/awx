import Base from '../Base';
import InstanceGroupsMixin from '../mixins/InstanceGroups.mixin';

class Inventories extends InstanceGroupsMixin(Base) {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/inventories/';

    this.readAccessList = this.readAccessList.bind(this);
    this.readHosts = this.readHosts.bind(this);
    this.readGroups = this.readGroups.bind(this);
    this.readGroupsOptions = this.readGroupsOptions.bind(this);
    this.promoteGroup = this.promoteGroup.bind(this);
  }

  readAccessList(id, params) {
    return this.http.get(`${this.baseUrl}${id}/access_list/`, {
      params,
    });
  }

  createHost(id, data) {
    return this.http.post(`${this.baseUrl}${id}/hosts/`, data);
  }

  readHosts(id, params) {
    return this.http.get(`${this.baseUrl}${id}/hosts/`, { params });
  }

  readGroups(id, params) {
    return this.http.get(`${this.baseUrl}${id}/groups/`, { params });
  }

  readGroupsOptions(id) {
    return this.http.options(`${this.baseUrl}${id}/groups/`);
  }

  promoteGroup(inventoryId, groupId) {
    return this.http.post(`${this.baseUrl}${inventoryId}/groups/`, {
      id: groupId,
      disassociate: true,
    });
  }
}

export default Inventories;
