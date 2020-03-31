import Base from '../Base';

class Schedules extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/schedules/';
  }

  createPreview(data) {
    return this.http.post(`${this.baseUrl}preview/`, data);
  }

  readCredentials(resourceId, params) {
    return this.http.get(`${this.baseUrl}${resourceId}/credentials/`, params);
  }

  readZoneInfo() {
    return this.http.get(`${this.baseUrl}zoneinfo/`);
  }
}

export default Schedules;
