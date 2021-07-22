function isEqual(array1, array2) {
  return (
    array1.length === array2.length &&
    array1.every((element, index) => element.id === array2[index].id)
  );
}

const InstanceGroupsMixin = (parent) =>
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

    async orderInstanceGroups(resourceId, current, original) {
      /* eslint-disable no-await-in-loop, no-restricted-syntax */
      // Resolve Promises sequentially to maintain order and avoid race condition
      if (!isEqual(current, original)) {
        for (const group of original) {
          await this.disassociateInstanceGroup(resourceId, group.id);
        }
        for (const group of current) {
          await this.associateInstanceGroup(resourceId, group.id);
        }
      }
    }
    /* eslint-enable no-await-in-loop, no-restricted-syntax */
  };

export default InstanceGroupsMixin;
