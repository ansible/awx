import Base from '../Base';

class JobTemplates extends Base {
  constructor (http) {
    super(http);
    this.baseUrl = '/api/v2/job_templates/';
  }
}

export default JobTemplates;
