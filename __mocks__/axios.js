import * as endpoints from '../src/endpoints';

const axios = require('axios');
const mockAPIConfigData = {
  data: {
    custom_virtualenvs: ['foo', 'bar'],
    ansible_version: "2.7.2",
    version: "2.1.1-40-g2758a3848"
  }
};
jest.genMockFromModule('axios');

axios.create = jest.fn(() => axios);
axios.get = jest.fn(() => axios);
axios.post = jest.fn(() => axios);
axios.create.mockReturnValue({
  get: axios.get,
  post: axios.post
});
axios.get.mockImplementation((endpoint) => {
  if (endpoint === endpoints.API_CONFIG) {
    return new Promise((resolve, reject) => {
      resolve(mockAPIConfigData);
    });
  }
  else {
    return 'get results';
  }
});
axios.post.mockResolvedValue('post results');

axios.customClearMocks = () => {
  axios.create.mockClear();
  axios.get.mockClear();
  axios.post.mockClear();
};

module.exports = axios;
