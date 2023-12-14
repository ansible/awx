import Base from '../Base';

class ReceptorAddresses extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = 'api/v2/receptor_addresses/';
  }
}

export default ReceptorAddresses;
