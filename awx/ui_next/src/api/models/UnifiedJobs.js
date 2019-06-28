import Base from '../Base';

class UnifiedJobs extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/unified_jobs/';
  }
}

export default UnifiedJobs;
