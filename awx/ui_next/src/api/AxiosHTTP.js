import axios from 'axios';

import { encodeQueryString } from '../util/qs';

const AxiosHTTP = axios.create({
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
  paramsSerializer(params) {
    return encodeQueryString(params);
  },
});

export default AxiosHTTP;
