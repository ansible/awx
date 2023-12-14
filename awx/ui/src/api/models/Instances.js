import Base from '../Base';

class Instances extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = 'api/v2/instances/';

    this.readHealthCheckDetail = this.readHealthCheckDetail.bind(this);
    this.healthCheck = this.healthCheck.bind(this);
    this.readInstanceGroup = this.readInstanceGroup.bind(this);
    this.readReceptorAddresses = this.readReceptorAddresses.bind(this);
    this.deprovisionInstance = this.deprovisionInstance.bind(this);
  }

  healthCheck(instanceId) {
    return this.http.post(`${this.baseUrl}${instanceId}/health_check/`);
  }

  readHealthCheckDetail(instanceId) {
    return this.http.get(`${this.baseUrl}${instanceId}/health_check/`);
  }

  readPeers(instanceId, params) {
    return this.http.get(`${this.baseUrl}${instanceId}/peers/`, { params });
  }

  readInstanceGroup(instanceId) {
    return this.http.get(`${this.baseUrl}${instanceId}/instance_groups/`);
  }

  readReceptorAddresses(instanceId) {
    return this.http.get(`${this.baseUrl}${instanceId}/receptor_addresses/`);
  }

  deprovisionInstance(instanceId) {
    return this.http.patch(`${this.baseUrl}${instanceId}/`, {
      node_state: 'deprovisioning',
    });
  }
}

export default Instances;
