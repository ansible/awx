import Base from '../Base';

class CredentialInputSources extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/credential_input_sources/';
  }
}

export default CredentialInputSources;
