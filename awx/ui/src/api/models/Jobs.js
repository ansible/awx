import Base from '../Base';
import RunnableMixin from '../mixins/Runnable.mixin';

class Jobs extends RunnableMixin(Base) {
  constructor(http) {
    super(http);
    this.baseUrl = 'api/v2/jobs/';
    this.jobEventSlug = '/job_events/';
  }

  cancel(id) {
    return this.http.post(`${this.baseUrl}${id}/cancel/`);
  }

  readCredentials(id) {
    return this.http.get(`${this.baseUrl}${id}/credentials/`);
  }

  readDetail(id) {
    return this.http.get(`${this.baseUrl}${id}/`);
  }

  readChildrenSummary(id) {
    return this.http.get(`${this.baseUrl}${id}/job_events/children_summary/`);
  }
}

export default Jobs;
