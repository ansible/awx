const axios = require('axios');

jest.genMockFromModule('axios');

axios.create = jest.fn(() => axios);
axios.get = jest.fn(() => axios);
axios.post = jest.fn(() => axios);
axios.create.mockReturnValue({
  get: axios.get,
  post: axios.post
});
axios.get.mockResolvedValue('get results');
axios.post.mockResolvedValue('post results');

axios.customClearMocks = () => {
  axios.create.mockClear();
  axios.get.mockClear();
  axios.post.mockClear();
};

module.exports = axios;
