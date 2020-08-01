import axios from 'axios';

import { encodeQueryString } from '../util/qs';

const defaultHttp = axios.create({
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
  paramsSerializer(params) {
    return encodeQueryString(params);
  },
});

class Base {
  constructor(http = defaultHttp, baseURL) {
    this.http = http;
    this.baseUrl = baseURL;
  }

  create(data) {
    return this.http.post(this.baseUrl, data);
  }

  destroy(id) {
    return this.http.delete(`${this.baseUrl}${id}/`);
  }

  read(params) {
    return this.http.get(this.baseUrl, {
      params,
    });
  }

  readDetail(id) {
    return this.http.get(`${this.baseUrl}${id}/`);
  }

  readOptions() {
    return this.http.options(this.baseUrl);
  }

  replace(id, data) {
    return this.http.put(`${this.baseUrl}${id}/`, data);
  }

  update(id, data) {
    return this.http.patch(`${this.baseUrl}${id}/`, data);
  }

  copy(id, data) {
    return this.http.post(`${this.baseUrl}${id}/copy/`, data);
  }
}

export default Base;
