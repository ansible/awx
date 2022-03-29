import Base from '../Base';

class Instances extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = 'api/v2/instances/';

    this.readHealthCheckDetail = this.readHealthCheckDetail.bind(this);
    this.healthCheck = this.healthCheck.bind(this);
    this.readInstanceGroup = this.readInstanceGroup.bind(this);
  }

  healthCheck(instanceId) {
    return this.http.post(`${this.baseUrl}${instanceId}/health_check/`);
  }

  readHealthCheckDetail(instanceId) {
    return this.http.get(`${this.baseUrl}${instanceId}/health_check/`);
  }

  readInstanceGroup(instanceId) {
    return this.http.get(`${this.baseUrl}${instanceId}/instance_groups/`);
  }
}

export default Instances;
