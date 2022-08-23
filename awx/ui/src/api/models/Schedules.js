import Base from '../Base';
import LabelsMixin from '../mixins/Labels.mixin';

class Schedules extends LabelsMixin(Base) {
  constructor(http) {
    super(http);
    this.baseUrl = 'api/v2/schedules/';
  }

  createPreview(data) {
    return this.http.post(`${this.baseUrl}preview/`, data);
  }

  readCredentials(resourceId, params) {
    return this.http.get(`${this.baseUrl}${resourceId}/credentials/`, params);
  }

  associateCredential(resourceId, credentialId) {
    return this.http.post(`${this.baseUrl}${resourceId}/credentials/`, {
      id: credentialId,
    });
  }

  disassociateCredential(resourceId, credentialId) {
    return this.http.post(`${this.baseUrl}${resourceId}/credentials/`, {
      id: credentialId,
      disassociate: true,
    });
  }

  readZoneInfo() {
    return this.http.get(`${this.baseUrl}zoneinfo/`);
  }
}

export default Schedules;
