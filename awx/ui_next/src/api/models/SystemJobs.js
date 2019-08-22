import Base from '../Base';

class SystemJobs extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/system_jobs/';
  }
}

export default SystemJobs;
