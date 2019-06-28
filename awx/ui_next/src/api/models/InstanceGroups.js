import Base from '../Base';

class InstanceGroups extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/instance_groups/';
  }
}

export default InstanceGroups;
