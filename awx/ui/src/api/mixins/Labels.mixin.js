const LabelsMixin = (parent) =>
  class extends parent {
    readLabels(id, params) {
      return this.http.get(`${this.baseUrl}${id}/labels/`, {
        params,
      });
    }

    readAllLabels(id) {
      const fetchLabels = async (pageNo = 1, labels = []) => {
        try {
          const { data } = await this.http.get(`${this.baseUrl}${id}/labels/`, {
            params: {
              page: pageNo,
              page_size: 200,
            },
          });
          if (data?.next) {
            return fetchLabels(pageNo + 1, labels.concat(data.results));
          }
          return Promise.resolve({
            data: {
              results: labels.concat(data.results),
            },
          });
        } catch (error) {
          return Promise.reject(error);
        }
      };

      return fetchLabels();
    }
  };

export default LabelsMixin;
