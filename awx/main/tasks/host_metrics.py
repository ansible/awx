import datetime
from dateutil.relativedelta import relativedelta
import logging

from django.conf import settings
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils.timezone import now
from rest_framework.fields import DateTimeField
from awx.main.dispatch import get_task_queuename
from awx.main.dispatch.publish import task
from awx.main.models.inventory import HostMetric, HostMetricSummaryMonthly
from awx.conf.license import get_license

logger = logging.getLogger('awx.main.tasks.host_metric_summary_monthly')


@task(queue=get_task_queuename)
def host_metric_summary_monthly():
    """Run cleanup host metrics summary monthly task each week"""
    if _is_run_threshold_reached(
        getattr(settings, 'HOST_METRIC_SUMMARY_TASK_LAST_TS', None), getattr(settings, 'HOST_METRIC_SUMMARY_TASK_INTERVAL', 7) * 86400
    ):
        logger.info(f"Executing host_metric_summary_monthly, last ran at {getattr(settings, 'HOST_METRIC_SUMMARY_TASK_LAST_TS', '---')}")
        HostMetricSummaryMonthlyTask().execute()
        logger.info("Finished host_metric_summary_monthly")


def _is_run_threshold_reached(setting, threshold_seconds):
    last_time = DateTimeField().to_internal_value(setting) if setting else DateTimeField().to_internal_value('1970-01-01')

    return (now() - last_time).total_seconds() > threshold_seconds


class HostMetricSummaryMonthlyTask:
    """
    This task computes last [threshold] months of HostMetricSummaryMonthly table
    [threshold] is setting CLEANUP_HOST_METRICS_HARD_THRESHOLD
    Each record in the table represents changes in HostMetric table in one month
    It always overrides all the months newer than <threshold>, never updates older months
    Algorithm:
    - hosts_added are HostMetric records with first_automation in given month
    - hosts_deleted are HostMetric records with deleted=True and last_deleted in given month
    - - HostMetrics soft-deleted before <threshold> also increases hosts_deleted in their last_deleted month
    - license_consumed is license_consumed(previous month) + hosts_added - hosts_deleted
    - - license_consumed for HostMetricSummaryMonthly.date < [threshold] is computed also from
        all HostMetrics.first_automation < [threshold]
    - license_capacity is set only for current month, and it's never updated (value taken from current subscription)
    """

    def __init__(self):
        self.host_metrics = {}
        self.processed_month = self._get_first_month()
        self.existing_summaries = None
        self.existing_summaries_idx = 0
        self.existing_summaries_cnt = 0
        self.records_to_create = []
        self.records_to_update = []

    def execute(self):
        self._load_existing_summaries()
        self._load_hosts_added()
        self._load_hosts_deleted()

        # Get first month after last hard delete
        month = self._get_first_month()
        license_consumed = self._get_license_consumed_before(month)

        # Fill record for each month
        while month <= datetime.date.today().replace(day=1):
            summary = self._find_or_create_summary(month)
            # Update summary and update license_consumed by hosts added/removed this month
            self._update_summary(summary, month, license_consumed)
            license_consumed = summary.license_consumed

            month = month + relativedelta(months=1)

        # Create/Update stats
        HostMetricSummaryMonthly.objects.bulk_create(self.records_to_create, batch_size=1000)
        HostMetricSummaryMonthly.objects.bulk_update(self.records_to_update, ['license_consumed', 'hosts_added', 'hosts_deleted'], batch_size=1000)

        # Set timestamp of last run
        settings.HOST_METRIC_SUMMARY_TASK_LAST_TS = now()

    def _get_license_consumed_before(self, month):
        license_consumed = 0
        for metric_month, metric in self.host_metrics.items():
            if metric_month < month:
                hosts_added = metric.get('hosts_added', 0)
                hosts_deleted = metric.get('hosts_deleted', 0)
                license_consumed = license_consumed + hosts_added - hosts_deleted
            else:
                break
        return license_consumed

    def _load_existing_summaries(self):
        """Find all summaries newer than host metrics delete threshold"""
        self.existing_summaries = HostMetricSummaryMonthly.objects.filter(date__gte=self._get_first_month()).order_by('date')
        self.existing_summaries_idx = 0
        self.existing_summaries_cnt = len(self.existing_summaries)

    def _load_hosts_added(self):
        """Aggregates hosts added each month, by the 'first_automation' timestamp"""
        #
        # -- SQL translation (for better code readability)
        # SELECT date_trunc('month', first_automation) as month,
        #        count(first_automation) AS hosts_added
        # FROM main_hostmetric
        # GROUP BY month
        # ORDER by month;
        result = (
            HostMetric.objects.annotate(month=TruncMonth('first_automation'))
            .values('month')
            .annotate(hosts_added=Count('first_automation'))
            .values('month', 'hosts_added')
            .order_by('month')
        )

        for host_metric in list(result):
            month = host_metric['month']
            if month:
                beginning_of_month = datetime.date(month.year, month.month, 1)
                if self.host_metrics.get(beginning_of_month) is None:
                    self.host_metrics[beginning_of_month] = {}
                self.host_metrics[beginning_of_month]['hosts_added'] = host_metric['hosts_added']

    def _load_hosts_deleted(self):
        """
        Aggregates hosts deleted each month, by the 'last_deleted' timestamp.
        Host metrics have to be deleted NOW to be counted as deleted before
        (by intention - statistics can change retrospectively by re-automation of previously deleted host)
        """
        #
        # -- SQL translation (for better code readability)
        # SELECT date_trunc('month', last_deleted) as month,
        #       count(last_deleted) AS hosts_deleted
        # FROM main_hostmetric
        # WHERE deleted = True
        # GROUP BY 1 # equal to "GROUP BY month"
        # ORDER by month;
        result = (
            HostMetric.objects.annotate(month=TruncMonth('last_deleted'))
            .values('month')
            .annotate(hosts_deleted=Count('last_deleted'))
            .values('month', 'hosts_deleted')
            .filter(deleted=True)
            .order_by('month')
        )
        for host_metric in list(result):
            month = host_metric['month']
            if month:
                beginning_of_month = datetime.date(month.year, month.month, 1)
                if self.host_metrics.get(beginning_of_month) is None:
                    self.host_metrics[beginning_of_month] = {}
                self.host_metrics[beginning_of_month]['hosts_deleted'] = host_metric['hosts_deleted']

    def _find_or_create_summary(self, month):
        summary = self._find_summary(month)

        if not summary:
            summary = HostMetricSummaryMonthly(date=month)
            self.records_to_create.append(summary)
        else:
            self.records_to_update.append(summary)
        return summary

    def _find_summary(self, month):
        """
        Existing summaries are ordered by month ASC.
        This method is called with month in ascending order too => only 1 traversing is enough
        """
        summary = None
        while not summary and self.existing_summaries_idx < self.existing_summaries_cnt:
            tmp = self.existing_summaries[self.existing_summaries_idx]
            if tmp.date < month:
                self.existing_summaries_idx += 1
            elif tmp.date == month:
                summary = tmp
            elif tmp.date > month:
                break
        return summary

    def _update_summary(self, summary, month, license_consumed):
        """Updates the metric with hosts added and deleted and set license info for current month"""
        # Get month counts from host metrics, zero if not found
        hosts_added, hosts_deleted = 0, 0
        if metric := self.host_metrics.get(month, None):
            hosts_added = metric.get('hosts_added', 0)
            hosts_deleted = metric.get('hosts_deleted', 0)

        summary.license_consumed = license_consumed + hosts_added - hosts_deleted
        summary.hosts_added = hosts_added
        summary.hosts_deleted = hosts_deleted

        # Set subscription count for current month
        if month == datetime.date.today().replace(day=1):
            license_info = get_license()
            summary.license_capacity = license_info.get('instance_count', 0)
        return summary

    @staticmethod
    def _get_first_month():
        """Returns first month after host metrics hard delete threshold"""
        threshold = getattr(settings, 'CLEANUP_HOST_METRICS_HARD_THRESHOLD', 36)
        return datetime.date.today().replace(day=1) - relativedelta(months=int(threshold) - 1)
