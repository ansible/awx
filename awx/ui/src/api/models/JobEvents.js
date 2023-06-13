import Base from '../Base';

class JobEvents extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = 'api/v2/job_events/';
  }

  readChildren(id, params) {
    return this.http.get(`${this.baseUrl}${id}/children/`, { params });
  }
}

export default JobEvents;
