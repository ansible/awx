import Base from '../Base';

class HostMetrics extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = 'api/v2/host_metrics/';
  }
}

export default HostMetrics;
