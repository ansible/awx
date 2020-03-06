const SchedulesMixin = parent =>
  class extends parent {
    readSchedules(id, params) {
      return this.http.get(`${this.baseUrl}${id}/schedules/`, { params });
    }

    readScheduleOptions(id) {
      return this.http.options(`${this.baseUrl}${id}/schedules/`);
    }
  };

export default SchedulesMixin;
