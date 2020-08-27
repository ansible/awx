import Base from '../Base';
import NotificationsMixin from '../mixins/Notifications.mixin';
import LaunchUpdateMixin from '../mixins/LaunchUpdate.mixin';
import SchedulesMixin from '../mixins/Schedules.mixin';

class Projects extends SchedulesMixin(
  LaunchUpdateMixin(NotificationsMixin(Base))
) {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/projects/';

    this.readAccessList = this.readAccessList.bind(this);
    this.readAccessOptions = this.readAccessOptions.bind(this);
    this.readInventories = this.readInventories.bind(this);
    this.readPlaybooks = this.readPlaybooks.bind(this);
    this.readSync = this.readSync.bind(this);
    this.sync = this.sync.bind(this);
  }

  readAccessList(id, params) {
    return this.http.get(`${this.baseUrl}${id}/access_list/`, { params });
  }

  readAccessOptions(id) {
    return this.http.options(`${this.baseUrl}${id}/access_list/`);
  }

  readInventories(id) {
    return this.http.get(`${this.baseUrl}${id}/inventories/`);
  }

  readPlaybooks(id) {
    return this.http.get(`${this.baseUrl}${id}/playbooks/`);
  }

  readSync(id) {
    return this.http.get(`${this.baseUrl}${id}/update/`);
  }

  sync(id) {
    return this.http.post(`${this.baseUrl}${id}/update/`);
  }
}

export default Projects;
