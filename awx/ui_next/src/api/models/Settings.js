import Base from '../Base';

class Settings extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/settings/';
  }

  readAllOptions() {
    return this.http.options(`${this.baseUrl}all/`);
  }

  updateAll(data) {
    return this.http.patch(`${this.baseUrl}all/`, data);
  }

  readCategory(category) {
    return this.http.get(`${this.baseUrl}${category}/`);
  }

  readCategoryOptions(category) {
    return this.http.options(`${this.baseUrl}${category}/`);
  }

  createTest(category, data) {
    return this.http.post(`${this.baseUrl}${category}/test/`, data);
  }
}

export default Settings;
