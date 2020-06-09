import Base from '../Base';

class Credentials extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/credentials/';

    this.readAccessList = this.readAccessList.bind(this);
    this.readAccessOptions = this.readAccessOptions.bind(this);
    this.readInputSources = this.readInputSources.bind(this);
  }

  readAccessList(id, params) {
    return this.http.get(`${this.baseUrl}${id}/access_list/`, {
      params,
    });
  }

  readAccessOptions(id) {
    return this.http.options(`${this.baseUrl}${id}/access_list/`);
  }

  readInputSources(id) {
    const fetchInputSources = async (pageNo = 1, inputSources = []) => {
      try {
        const { data } = await this.http.get(
          `${this.baseUrl}${id}/input_sources/`,
          {
            params: {
              page: pageNo,
              page_size: 200,
            },
          }
        );
        if (data.next) {
          return fetchInputSources(
            pageNo + 1,
            inputSources.concat(data.results)
          );
        }
        return Promise.resolve(inputSources.concat(data.results));
      } catch (error) {
        return Promise.reject(error);
      }
    };

    return fetchInputSources();
  }

  test(id, data) {
    return this.http.post(`${this.baseUrl}${id}/test/`, data);
  }
}

export default Credentials;
