import Base from '../Base';

class Settings extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = 'api/v2/settings/';
  }

  readAllOptions() {
    return this.http.options(`${this.baseUrl}all/`);
  }

  updateAll(data) {
    return this.http.patch(`${this.baseUrl}all/`, data);
  }

  readAll() {
    return this.http.get(`${this.baseUrl}all/`);
  }

  updateCategory(category, data) {
    return this.http.patch(`${this.baseUrl}${category}/`, data);
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

  revertCategory(category) {
    return this.http.delete(`${this.baseUrl}${category}/`);
  }
}

export default Settings;
