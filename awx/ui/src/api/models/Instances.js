import Base from '../Base';

class Instances extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/instances/';

    this.readHealthCheckDetail = this.readHealthCheckDetail.bind(this);
    this.createHealthCheck = this.createHealthCheck.bind(this);
  }

  createHealthCheck(instanceId) {
    return this.http.post(`${this.baseUrl}${instanceId}/health_check/`);
  }

  readHealthCheckDetail(instanceId) {
    return this.http.get(`${this.baseUrl}${instanceId}/health_check/`);
  }
}

export default Instances;
