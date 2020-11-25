import Base from '../Base';

class Dashboard extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/dashboard/';
  }

  readJobGraph(params) {
    return this.http.get(`${this.baseUrl}graphs/jobs/`, {
      params,
    });
  }
}

export default Dashboard;
