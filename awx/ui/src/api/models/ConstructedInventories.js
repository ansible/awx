import Base from '../Base';
import InstanceGroupsMixin from '../mixins/InstanceGroups.mixin';

class ConstructedInventories extends InstanceGroupsMixin(Base) {
  constructor(http) {
    super(http);
    this.baseUrl = 'api/v2/constructed_inventories/';
  }

  async readConstructedInventoryOptions(id, method) {
    const {
      data: { actions },
    } = await this.http.options(`${this.baseUrl}${id}/`);

    if (actions[method]) {
      return actions[method];
    }

    throw new Error(
      `You have insufficient access to this Constructed Inventory. 
      Please contact your system administrator if there is an issue with your access.`
    );
  }
}
export default ConstructedInventories;
