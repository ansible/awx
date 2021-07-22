import Base from '../Base';
import NotificationsMixin from '../mixins/Notifications.mixin';
import SchedulesMixin from '../mixins/Schedules.mixin';

const Mixins = SchedulesMixin(NotificationsMixin(Base));

class SystemJobTemplates extends Mixins {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/system_job_templates/';
  }

  readDetail(id) {
    const path = `${this.baseUrl}${id}/`;

    return this.http.get(path).then(({ data }) => data);
  }

  launch(id, data) {
    return this.http.post(`${this.baseUrl}${id}/launch/`, data);
  }
}

export default SystemJobTemplates;
