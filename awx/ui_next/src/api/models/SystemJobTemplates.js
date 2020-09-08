import Base from '../Base';

class SystemJobTemplates extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/system_job_templates/';
  }

  readDetail(id) {
    return this.http.get(`${this.baseUrl}${id}/`).then(({ data }) => data);
  }
}

export default SystemJobTemplates;
