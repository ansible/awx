import Base from '../Base';
import InstanceGroupsMixin from '../mixins/InstanceGroups.mixin';

class ConstructedInventories extends InstanceGroupsMixin(Base) {
  constructor(http) {
    super(http);
    this.baseUrl = 'api/v2/constructed_inventories/';
  }
}
export default ConstructedInventories;
