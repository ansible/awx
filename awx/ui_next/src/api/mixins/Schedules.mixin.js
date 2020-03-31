const SchedulesMixin = parent =>
  class extends parent {
    createSchedule(id, data) {
      return this.http.post(`${this.baseUrl}${id}/schedules/`, data);
    }

    readSchedules(id, params) {
      return this.http.get(`${this.baseUrl}${id}/schedules/`, { params });
    }

    readScheduleOptions(id) {
      return this.http.options(`${this.baseUrl}${id}/schedules/`);
    }
  };

export default SchedulesMixin;
