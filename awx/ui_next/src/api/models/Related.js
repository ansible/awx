import AxiosHTTP from '../AxiosHTTP';

class Related {
  constructor(http = AxiosHTTP) {
    this.http = http;
  }

  delete(relatedEndpoint) {
    return this.http.delete(relatedEndpoint);
  }

  get(relatedEndpoint, params) {
    return this.http.get(relatedEndpoint, {
      params,
    });
  }

  patch(relatedEndpoint, data) {
    return this.http.patch(relatedEndpoint, data);
  }

  post(relatedEndpoint, data) {
    return this.http.post(relatedEndpoint, data);
  }

  put(relatedEndpoint, data) {
    return this.http.put(relatedEndpoint, data);
  }
}

export default Related;
