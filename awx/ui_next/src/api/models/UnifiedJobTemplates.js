import Base from '../Base';

class UnifiedJobTemplates extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/unified_job_templates/';
  }
}

export default UnifiedJobTemplates;
