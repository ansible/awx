import Base from '../Base';
import RunnableMixin from '../mixins/Runnable.mixin';

class ProjectUpdates extends RunnableMixin(Base) {
  constructor(http) {
    super(http);
    this.baseUrl = 'api/v2/project_updates/';
  }

  readCredentials(id) {
    return this.http.get(`${this.baseUrl}${id}/credentials/`);
  }
}

export default ProjectUpdates;
