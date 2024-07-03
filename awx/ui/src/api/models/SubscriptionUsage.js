import Base from '../Base';

class SubscriptionUsage extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = 'api/v2/host_metric_summary_monthly/';
  }

  readSubscriptionUsageChart(dateRange) {
    return this.http.get(
      `${this.baseUrl}?date__gte=${dateRange}&order_by=date&page_size=100`
    );
  }
}

export default SubscriptionUsage;
