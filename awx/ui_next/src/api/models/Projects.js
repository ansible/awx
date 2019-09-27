import Base from '../Base';
import LaunchUpdateMixin from '../mixins/LaunchUpdate.mixin';

class Projects extends LaunchUpdateMixin(Base) {
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
