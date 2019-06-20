import Base from '../Base';

class JobTemplates extends Base {
  constructor (http) {
    super(http);
    this.baseUrl = '/api/v2/job_templates/';

    this.launch = this.launch.bind(this);
    this.readLaunch = this.readLaunch.bind(this);
  }

  launch (id, data) {
    return this.http.post(`${this.baseUrl}${id}/launch/`, data);
  }

  readLaunch (id) {
    return this.http.get(`${this.baseUrl}${id}/launch/`);
  }
}

export default JobTemplates;
