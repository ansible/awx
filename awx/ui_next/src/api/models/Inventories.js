import Base from '../Base';
import InstanceGroupsMixin from '../mixins/InstanceGroups.mixin';

class Inventories extends InstanceGroupsMixin(Base) {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/inventories/';

    this.readAccessList = this.readAccessList.bind(this);
    this.readAccessOptions = this.readAccessOptions.bind(this);
    this.readHosts = this.readHosts.bind(this);
    this.readHostDetail = this.readHostDetail.bind(this);
    this.readGroups = this.readGroups.bind(this);
    this.readGroupsOptions = this.readGroupsOptions.bind(this);
    this.promoteGroup = this.promoteGroup.bind(this);
  }

  readAccessList(id, params) {
    return this.http.get(`${this.baseUrl}${id}/access_list/`, {
      params,
    });
  }

  readAccessOptions(id) {
    return this.http.options(`${this.baseUrl}${id}/access_list/`);
  }

  createHost(id, data) {
    return this.http.post(`${this.baseUrl}${id}/hosts/`, data);
  }

  readHosts(id, params) {
    return this.http.get(`${this.baseUrl}${id}/hosts/`, {
      params,
    });
  }

  async readHostDetail(inventoryId, hostId) {
    const {
      data: { results },
    } = await this.http.get(
      `${this.baseUrl}${inventoryId}/hosts/?id=${hostId}`
    );

    if (Array.isArray(results) && results.length) {
      return results[0];
    }

    throw new Error(
      `How did you get here? Host not found for Inventory ID: ${inventoryId}`
    );
  }

  readGroups(id, params) {
    return this.http.get(`${this.baseUrl}${id}/groups/`, {
      params,
    });
  }

  readGroupsOptions(id) {
    return this.http.options(`${this.baseUrl}${id}/groups/`);
  }

  readHostsOptions(id) {
    return this.http.options(`${this.baseUrl}${id}/hosts/`);
  }

  promoteGroup(inventoryId, groupId) {
    return this.http.post(`${this.baseUrl}${inventoryId}/groups/`, {
      id: groupId,
      disassociate: true,
    });
  }

  readSources(inventoryId, params) {
    return this.http.get(`${this.baseUrl}${inventoryId}/inventory_sources/`, {
      params,
    });
  }

  async readSourceDetail(inventoryId, sourceId) {
    const {
      data: { results },
    } = await this.http.get(
      `${this.baseUrl}${inventoryId}/inventory_sources/?id=${sourceId}`
    );

    if (Array.isArray(results) && results.length) {
      return results[0];
    }

    throw new Error(
      `How did you get here? Source not found for Inventory ID: ${inventoryId}`
    );
  }

  syncAllSources(inventoryId) {
    return this.http.post(
      `${this.baseUrl}${inventoryId}/update_inventory_sources/`
    );
  }

  readAdHocOptions(inventoryId) {
    return this.http.options(`${this.baseUrl}${inventoryId}/ad_hoc_commands/`);
  }

  launchAdHocCommands(inventoryId, values) {
    return this.http.post(
      `${this.baseUrl}${inventoryId}/ad_hoc_commands/`,
      values
    );
  }
}

export default Inventories;
