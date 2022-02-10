import Base from '../Base';

import RunnableMixin from '../mixins/Runnable.mixin';

class SystemJobs extends RunnableMixin(Base) {
  constructor(http) {
    super(http);
    this.baseUrl = 'api/v2/system_jobs/';
  }

  readCredentials(id) {
    return this.http.get(`${this.baseUrl}${id}/credentials/`);
  }
}

export default SystemJobs;
