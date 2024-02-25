import pytest
import datetime
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.utils import timezone


from awx.main.management.commands.host_metric_summary_monthly import Command
from awx.main.models.inventory import HostMetric, HostMetricSummaryMonthly
from awx.main.tests.factories.fixtures import mk_host_metric, mk_host_metric_summary


@pytest.fixture
def threshold():
    return int(getattr(settings, 'CLEANUP_HOST_METRICS_HARD_THRESHOLD', 36))


@pytest.mark.django_db
@pytest.mark.parametrize("metrics_cnt", [0, 1, 2, 3])
@pytest.mark.parametrize("mode", ["old_data", "actual_data", "all_data"])
def test_summaries_counts(threshold, metrics_cnt, mode):
    assert HostMetricSummaryMonthly.objects.count() == 0

    for idx in range(metrics_cnt):
        if mode == "old_data" or mode == "all_data":
            mk_host_metric(None, months_ago(threshold + idx, "dt"))
        elif mode == "actual_data" or mode == "all_data":
            mk_host_metric(None, (months_ago(threshold - idx, "dt")))

    Command().handle()

    # Number of records is equal to host metrics' hard cleanup months
    assert HostMetricSummaryMonthly.objects.count() == threshold

    # Records start with date in the month following to the threshold month
    date = months_ago(threshold - 1)
    for metric in list(HostMetricSummaryMonthly.objects.order_by('date').all()):
        assert metric.date == date
        date += relativedelta(months=1)

    # Older record are untouched
    mk_host_metric_summary(date=months_ago(threshold + 10))
    Command().handle()

    assert HostMetricSummaryMonthly.objects.count() == threshold + 1


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["old_data", "actual_data", "all_data"])
def test_summary_values(threshold, mode):
    tester = {"old_data": MetricsTesterOldData(threshold), "actual_data": MetricsTesterActualData(threshold), "all_data": MetricsTesterCombinedData(threshold)}[
        mode
    ]

    for iteration in ["create_metrics", "add_old_summaries", "change_metrics", "delete_metrics", "add_metrics"]:
        getattr(tester, iteration)()  # call method by string

        # Operation is idempotent, repeat twice
        for _ in range(2):
            Command().handle()
            # call assert method by string
            getattr(tester, f"assert_{iteration}")()


class MetricsTester:
    def __init__(self, threshold, ignore_asserts=False):
        self.threshold = threshold
        self.expected_summaries = {}
        self.ignore_asserts = ignore_asserts

    def add_old_summaries(self):
        """These records don't correspond with Host metrics"""
        mk_host_metric_summary(self.below(4), license_consumed=100, hosts_added=10, hosts_deleted=5)
        mk_host_metric_summary(self.below(3), license_consumed=105, hosts_added=20, hosts_deleted=10)
        mk_host_metric_summary(self.below(2), license_consumed=115, hosts_added=60, hosts_deleted=75)

    def assert_add_old_summaries(self):
        """Old summary records should be untouched"""
        self.expected_summaries[self.below(4)] = {"date": self.below(4), "license_consumed": 100, "hosts_added": 10, "hosts_deleted": 5}
        self.expected_summaries[self.below(3)] = {"date": self.below(3), "license_consumed": 105, "hosts_added": 20, "hosts_deleted": 10}
        self.expected_summaries[self.below(2)] = {"date": self.below(2), "license_consumed": 115, "hosts_added": 60, "hosts_deleted": 75}

        self.assert_host_metric_summaries()

    def assert_host_metric_summaries(self):
        """Ignore asserts when old/actual test object is used only as a helper for Combined test"""
        if self.ignore_asserts:
            return True

        for summary in list(HostMetricSummaryMonthly.objects.order_by('date').all()):
            assert self.expected_summaries.get(summary.date, None) is not None

            assert self.expected_summaries[summary.date] == {
                "date": summary.date,
                "license_consumed": summary.license_consumed,
                "hosts_added": summary.hosts_added,
                "hosts_deleted": summary.hosts_deleted,
            }

    def below(self, months, fmt="date"):
        """months below threshold, returns first date of that month"""
        date = months_ago(self.threshold + months)
        if fmt == "dt":
            return timezone.make_aware(datetime.datetime.combine(date, datetime.datetime.min.time()))
        else:
            return date

    def above(self, months, fmt="date"):
        """months above threshold, returns first date of that month"""
        date = months_ago(self.threshold - months)
        if fmt == "dt":
            return timezone.make_aware(datetime.datetime.combine(date, datetime.datetime.min.time()))
        else:
            return date


class MetricsTesterOldData(MetricsTester):
    def create_metrics(self):
        """Creates 7 host metrics older than delete threshold"""
        mk_host_metric("host_1", first_automation=self.below(3, "dt"))
        mk_host_metric("host_2", first_automation=self.below(2, "dt"))
        mk_host_metric("host_3", first_automation=self.below(2, "dt"), last_deleted=self.above(2, "dt"), deleted=False)
        mk_host_metric("host_4", first_automation=self.below(2, "dt"), last_deleted=self.above(2, "dt"), deleted=True)
        mk_host_metric("host_5", first_automation=self.below(2, "dt"), last_deleted=self.below(2, "dt"), deleted=True)
        mk_host_metric("host_6", first_automation=self.below(1, "dt"), last_deleted=self.below(1, "dt"), deleted=False)
        mk_host_metric("host_7", first_automation=self.below(1, "dt"))

    def assert_create_metrics(self):
        """
        Month 1 is computed from older host metrics,
        Month 2 has deletion (host_4)
        Other months are unchanged (same as month 2)
        """
        self.expected_summaries = {
            self.above(1): {"date": self.above(1), "license_consumed": 6, "hosts_added": 0, "hosts_deleted": 0},
            self.above(2): {"date": self.above(2), "license_consumed": 5, "hosts_added": 0, "hosts_deleted": 1},
        }
        # no change in months 3+
        idx = 3
        month = self.above(idx)
        while month <= beginning_of_the_month():
            self.expected_summaries[self.above(idx)] = {"date": self.above(idx), "license_consumed": 5, "hosts_added": 0, "hosts_deleted": 0}
            month += relativedelta(months=1)
            idx += 1

        self.assert_host_metric_summaries()

    def add_old_summaries(self):
        super().add_old_summaries()

    def assert_add_old_summaries(self):
        super().assert_add_old_summaries()

    @staticmethod
    def change_metrics():
        """Hosts 1,2 soft deleted, host_4 automated again (undeleted)"""
        HostMetric.objects.filter(hostname='host_1').update(last_deleted=beginning_of_the_month("dt"), deleted=True)
        HostMetric.objects.filter(hostname='host_2').update(last_deleted=timezone.now(), deleted=True)
        HostMetric.objects.filter(hostname='host_4').update(deleted=False)

    def assert_change_metrics(self):
        """
        Summaries since month 2 were changed (host_4 restored == automated again)
        Current month has 2 deletions (host_1, host_2)
        """
        self.expected_summaries[self.above(2)] |= {'hosts_deleted': 0}
        for idx in range(2, self.threshold):
            self.expected_summaries[self.above(idx)] |= {'license_consumed': 6}
        self.expected_summaries[beginning_of_the_month()] |= {'license_consumed': 4, 'hosts_deleted': 2}

        self.assert_host_metric_summaries()

    @staticmethod
    def delete_metrics():
        """Deletes metric deleted before the threshold"""
        HostMetric.objects.filter(hostname='host_5').delete()

    def assert_delete_metrics(self):
        """No change"""
        self.assert_host_metric_summaries()

    @staticmethod
    def add_metrics():
        """Adds new metrics"""
        mk_host_metric("host_24", first_automation=beginning_of_the_month("dt"))
        mk_host_metric("host_25", first_automation=beginning_of_the_month("dt"))  # timezone.now())

    def assert_add_metrics(self):
        """Summary in current month is updated"""
        self.expected_summaries[beginning_of_the_month()]['license_consumed'] = 6
        self.expected_summaries[beginning_of_the_month()]['hosts_added'] = 2

        self.assert_host_metric_summaries()


class MetricsTesterActualData(MetricsTester):
    def create_metrics(self):
        """Creates 16 host metrics newer than delete threshold"""
        mk_host_metric("host_8", first_automation=self.above(1, "dt"))
        mk_host_metric("host_9", first_automation=self.above(1, "dt"), last_deleted=self.above(1, "dt"))
        mk_host_metric("host_10", first_automation=self.above(1, "dt"), last_deleted=self.above(1, "dt"), deleted=True)
        mk_host_metric("host_11", first_automation=self.above(1, "dt"), last_deleted=self.above(2, "dt"))
        mk_host_metric("host_12", first_automation=self.above(1, "dt"), last_deleted=self.above(2, "dt"), deleted=True)
        mk_host_metric("host_13", first_automation=self.above(2, "dt"))
        mk_host_metric("host_14", first_automation=self.above(2, "dt"), last_deleted=self.above(2, "dt"))
        mk_host_metric("host_15", first_automation=self.above(2, "dt"), last_deleted=self.above(2, "dt"), deleted=True)
        mk_host_metric("host_16", first_automation=self.above(2, "dt"), last_deleted=self.above(3, "dt"))
        mk_host_metric("host_17", first_automation=self.above(2, "dt"), last_deleted=self.above(3, "dt"), deleted=True)
        mk_host_metric("host_18", first_automation=self.above(4, "dt"))
        # next one shouldn't happen in real (deleted=True, last_deleted = NULL)
        mk_host_metric("host_19", first_automation=self.above(4, "dt"), deleted=True)
        mk_host_metric("host_20", first_automation=self.above(4, "dt"), last_deleted=self.above(4, "dt"))
        mk_host_metric("host_21", first_automation=self.above(4, "dt"), last_deleted=self.above(4, "dt"), deleted=True)
        mk_host_metric("host_22", first_automation=self.above(4, "dt"), last_deleted=self.above(5, "dt"))
        mk_host_metric("host_23", first_automation=self.above(4, "dt"), last_deleted=self.above(5, "dt"), deleted=True)

    def assert_create_metrics(self):
        self.expected_summaries = {
            self.above(1): {"date": self.above(1), "license_consumed": 4, "hosts_added": 5, "hosts_deleted": 1},
            self.above(2): {"date": self.above(2), "license_consumed": 7, "hosts_added": 5, "hosts_deleted": 2},
            self.above(3): {"date": self.above(3), "license_consumed": 6, "hosts_added": 0, "hosts_deleted": 1},
            self.above(4): {"date": self.above(4), "license_consumed": 11, "hosts_added": 6, "hosts_deleted": 1},
            self.above(5): {"date": self.above(5), "license_consumed": 10, "hosts_added": 0, "hosts_deleted": 1},
        }
        # no change in months 6+
        idx = 6
        month = self.above(idx)
        while month <= beginning_of_the_month():
            self.expected_summaries[self.above(idx)] = {"date": self.above(idx), "license_consumed": 10, "hosts_added": 0, "hosts_deleted": 0}
            month += relativedelta(months=1)
            idx += 1

        self.assert_host_metric_summaries()

    def add_old_summaries(self):
        super().add_old_summaries()

    def assert_add_old_summaries(self):
        super().assert_add_old_summaries()

    @staticmethod
    def change_metrics():
        """
        - Hosts 12, 19, 21 were automated again (undeleted)
        - Host 16 was soft deleted
        - Host 17 was undeleted and soft deleted again
        """
        HostMetric.objects.filter(hostname='host_12').update(deleted=False)
        HostMetric.objects.filter(hostname='host_16').update(last_deleted=timezone.now(), deleted=True)
        HostMetric.objects.filter(hostname='host_17').update(last_deleted=beginning_of_the_month("dt"), deleted=True)
        HostMetric.objects.filter(hostname='host_19').update(deleted=False)
        HostMetric.objects.filter(hostname='host_21').update(deleted=False)

    def assert_change_metrics(self):
        """
        Summaries since month 2 were changed
        Current month has 2 deletions (host_16, host_17)
        """
        self.expected_summaries[self.above(2)] |= {'license_consumed': 8, 'hosts_deleted': 1}
        self.expected_summaries[self.above(3)] |= {'license_consumed': 8, 'hosts_deleted': 0}
        self.expected_summaries[self.above(4)] |= {'license_consumed': 14, 'hosts_deleted': 0}

        # month 5 had hosts_deleted 1 => license_consumed == 14 - 1
        for idx in range(5, self.threshold):
            self.expected_summaries[self.above(idx)] |= {'license_consumed': 13}
        self.expected_summaries[beginning_of_the_month()] |= {'license_consumed': 11, 'hosts_deleted': 2}

        self.assert_host_metric_summaries()

    def delete_metrics(self):
        """Hard cleanup can't delete metrics newer than threshold. No change"""
        pass

    def assert_delete_metrics(self):
        """No change"""
        self.assert_host_metric_summaries()

    @staticmethod
    def add_metrics():
        """Adds new metrics"""
        mk_host_metric("host_26", first_automation=beginning_of_the_month("dt"))
        mk_host_metric("host_27", first_automation=timezone.now())

    def assert_add_metrics(self):
        """
        Two metrics were deleted in current month by change_metrics()
        Two metrics are added now
        => license_consumed is equal to the previous month (13 - 2 + 2)
        """
        self.expected_summaries[beginning_of_the_month()] |= {'license_consumed': 13, 'hosts_added': 2}

        self.assert_host_metric_summaries()


class MetricsTesterCombinedData(MetricsTester):
    def __init__(self, threshold):
        super().__init__(threshold)
        self.old_data = MetricsTesterOldData(threshold, ignore_asserts=True)
        self.actual_data = MetricsTesterActualData(threshold, ignore_asserts=True)

    def assert_host_metric_summaries(self):
        self._combine_expected_summaries()
        super().assert_host_metric_summaries()

    def create_metrics(self):
        self.old_data.create_metrics()
        self.actual_data.create_metrics()

    def assert_create_metrics(self):
        self.old_data.assert_create_metrics()
        self.actual_data.assert_create_metrics()

        self.assert_host_metric_summaries()

    def add_old_summaries(self):
        super().add_old_summaries()

    def assert_add_old_summaries(self):
        self.old_data.assert_add_old_summaries()
        self.actual_data.assert_add_old_summaries()

        self.assert_host_metric_summaries()

    def change_metrics(self):
        self.old_data.change_metrics()
        self.actual_data.change_metrics()

    def assert_change_metrics(self):
        self.old_data.assert_change_metrics()
        self.actual_data.assert_change_metrics()

        self.assert_host_metric_summaries()

    def delete_metrics(self):
        self.old_data.delete_metrics()
        self.actual_data.delete_metrics()

    def assert_delete_metrics(self):
        self.old_data.assert_delete_metrics()
        self.actual_data.assert_delete_metrics()

        self.assert_host_metric_summaries()

    def add_metrics(self):
        self.old_data.add_metrics()
        self.actual_data.add_metrics()

    def assert_add_metrics(self):
        self.old_data.assert_add_metrics()
        self.actual_data.assert_add_metrics()

        self.assert_host_metric_summaries()

    def _combine_expected_summaries(self):
        """
        Expected summaries are sum of expected values for tests with old and actual data
        Except data older than hard delete threshold (these summaries are untouched by task => the same in all tests)
        """
        for date, summary in self.old_data.expected_summaries.items():
            if date <= months_ago(self.threshold):
                license_consumed = summary['license_consumed']
                hosts_added = summary['hosts_added']
                hosts_deleted = summary['hosts_deleted']
            else:
                license_consumed = summary['license_consumed'] + self.actual_data.expected_summaries[date]['license_consumed']
                hosts_added = summary['hosts_added'] + self.actual_data.expected_summaries[date]['hosts_added']
                hosts_deleted = summary['hosts_deleted'] + self.actual_data.expected_summaries[date]['hosts_deleted']
            self.expected_summaries[date] = {'date': date, 'license_consumed': license_consumed, 'hosts_added': hosts_added, 'hosts_deleted': hosts_deleted}


def months_ago(num, fmt="date"):
    if num is None:
        return None
    return beginning_of_the_month(fmt) - relativedelta(months=num)


def beginning_of_the_month(fmt="date"):
    date = datetime.date.today().replace(day=1)
    if fmt == "dt":
        return timezone.make_aware(datetime.datetime.combine(date, datetime.datetime.min.time()))
    else:
        return date
