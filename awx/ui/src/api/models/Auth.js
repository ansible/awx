import Base from '../Base';

class Auth extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = 'api/v2/auth/';
  }
}

export default Auth;
