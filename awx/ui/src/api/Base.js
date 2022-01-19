/* eslint-disable default-param-last */
import axios from 'axios';
import { encodeQueryString } from 'util/qs';
import debounce from 'util/debounce';
import { SESSION_TIMEOUT_KEY } from '../constants';

const updateStorage = debounce((key, val) => {
  window.localStorage.setItem(key, val);
  window.dispatchEvent(new Event('storage'));
}, 500);

const defaultHttp = axios.create({
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
  paramsSerializer(params) {
    return encodeQueryString(params);
  },
});

defaultHttp.interceptors.response.use((response) => {
  const timeout = response?.headers['session-timeout'];
  if (timeout) {
    const timeoutDate = new Date().getTime() + timeout * 1000;
    updateStorage(SESSION_TIMEOUT_KEY, String(timeoutDate));
  }
  return response;
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
