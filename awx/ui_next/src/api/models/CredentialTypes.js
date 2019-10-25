import Base from '../Base';

class CredentialTypes extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/credential_types/';
  }
}

export default CredentialTypes;
