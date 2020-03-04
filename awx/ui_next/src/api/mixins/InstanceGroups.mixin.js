const InstanceGroupsMixin = parent =>
  class extends parent {
    readInstanceGroups(resourceId, params) {
      return this.http.get(`${this.baseUrl}${resourceId}/instance_groups/`, {
        params,
      });
    }

    associateInstanceGroup(resourceId, instanceGroupId) {
      return this.http.post(`${this.baseUrl}${resourceId}/instance_groups/`, {
        id: instanceGroupId,
      });
    }

    disassociateInstanceGroup(resourceId, instanceGroupId) {
      return this.http.post(`${this.baseUrl}${resourceId}/instance_groups/`, {
        id: instanceGroupId,
        disassociate: true,
      });
    }
  };

export default InstanceGroupsMixin;
