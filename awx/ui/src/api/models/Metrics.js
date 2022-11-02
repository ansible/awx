import Base from '../Base';

class Metrics extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = 'api/v2/metrics/';
  }
}
export default Metrics;
