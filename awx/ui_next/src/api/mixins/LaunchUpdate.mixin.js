const LaunchUpdateMixin = parent =>
  class extends parent {
    launchUpdate(id, data) {
      return this.http.post(`${this.baseUrl}${id}/update/`, data);
    }

    readLaunchUpdate(id) {
      return this.http.get(`${this.baseUrl}${id}/update/`);
    }
  };

export default LaunchUpdateMixin;
