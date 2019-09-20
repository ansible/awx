const RelaunchMixin = parent =>
  class extends parent {
    relaunch(id, data) {
      return this.http.post(`${this.baseUrl}${id}/relaunch/`, data);
    }

    readRelaunch(id) {
      return this.http.get(`${this.baseUrl}${id}/relaunch/`);
    }
  };

export default RelaunchMixin;
