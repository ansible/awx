import Base from '../Base';

class NotificationTemplates extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/notification_templates/';
  }

  test(id) {
    return this.http.post(`${this.baseUrl}${id}/test/`);
  }
}

export default NotificationTemplates;
