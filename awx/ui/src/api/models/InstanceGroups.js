import Base from '../Base';

class InstanceGroups extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/instance_groups/';

    this.associateInstance = this.associateInstance.bind(this);
    this.disassociateInstance = this.disassociateInstance.bind(this);
    this.readInstanceOptions = this.readInstanceOptions.bind(this);
    this.readInstances = this.readInstances.bind(this);
    this.readJobs = this.readJobs.bind(this);
  }

  associateInstance(instanceGroupId, instanceId) {
    return this.http.post(`${this.baseUrl}${instanceGroupId}/instances/`, {
      id: instanceId,
    });
  }

  disassociateInstance(instanceGroupId, instanceId) {
    return this.http.post(`${this.baseUrl}${instanceGroupId}/instances/`, {
      id: instanceId,
      disassociate: true,
    });
  }

  readInstances(id, params) {
    return this.http.get(`${this.baseUrl}${id}/instances/`, { params });
  }

  readInstanceOptions(id) {
    return this.http.options(`${this.baseUrl}${id}/instances/`);
  }

  readJobs(id) {
    return this.http.get(`${this.baseUrl}${id}/jobs/`);
  }
}

export default InstanceGroups;
