import Base from '../Base';

class Projects extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/projects/';

    this.readPlaybooks = this.readPlaybooks.bind(this);
  }

  readPlaybooks(id) {
    return this.http.get(`${this.baseUrl}${id}/playbooks/`);
  }
}

export default Projects;
