import Base from '../Base';

class CredentialTypes extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/credential_types/';
  }

  async loadAllTypes(
    acceptableKinds = ['machine', 'cloud', 'net', 'ssh', 'vault', 'kubernetes']
  ) {
    const pageSize = 200;
    // The number of credential types a user can have is unlimited. In practice, it is unlikely for
    // users to have more than a page at the maximum request size.
    const {
      data: { next, results },
    } = await this.read({ page_size: pageSize });
    let nextResults = [];
    if (next) {
      const { data } = await this.read({
        page_size: pageSize,
        page: 2,
      });
      nextResults = data.results;
    }
    return results
      .concat(nextResults)
      .filter(type => acceptableKinds.includes(type.kind));
  }

  test(id, data) {
    return this.http.post(`${this.baseUrl}${id}/test/`, data);
  }
}

export default CredentialTypes;
