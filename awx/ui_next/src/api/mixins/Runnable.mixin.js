const Runnable = (parent) =>
  class extends parent {
    jobEventSlug = '/events/';

    cancel(id) {
      const endpoint = `${this.baseUrl}${id}/cancel/`;

      return this.http.post(endpoint);
    }

    launchUpdate(id, data) {
      const endpoint = `${this.baseUrl}${id}/update/`;

      return this.http.post(endpoint, data);
    }

    readLaunchUpdate(id) {
      const endpoint = `${this.baseUrl}${id}/update/`;

      return this.http.get(endpoint);
    }

    readEvents(id, params = {}) {
      const endpoint = `${this.baseUrl}${id}${this.jobEventSlug}`;

      return this.http.get(endpoint, { params });
    }

    readEventOptions(id) {
      const endpoint = `${this.baseUrl}${id}${this.jobEventSlug}`;

      return this.http.options(endpoint);
    }

    readRelaunch(id) {
      const endpoint = `${this.baseUrl}${id}/relaunch/`;

      return this.http.get(endpoint);
    }

    relaunch(id, data) {
      const endpoint = `${this.baseUrl}${id}/relaunch/`;

      return this.http.post(endpoint, data);
    }
  };

export default Runnable;
