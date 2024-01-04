import Base from '../Base';

class ReceptorAddresses extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = 'api/v2/receptor_addresses/';
  }

  updateReceptorAddresses(instanceId, data) {
    return this.http.post(`${this.baseUrl}`, data);
  }
}

export default ReceptorAddresses;
