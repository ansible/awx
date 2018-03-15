from django.db import models


class FSMTrace(models.Model):

    fsm_trace_id = models.AutoField(primary_key=True,)
    fsm_name = models.CharField(max_length=200, blank=True)
    from_state = models.CharField(max_length=200, blank=True)
    to_state = models.CharField(max_length=200, blank=True)
    message_type = models.CharField(max_length=200, blank=True)
    client = models.ForeignKey('network_ui.Client',)
    trace_session_id = models.IntegerField(default=0,)
    order = models.IntegerField(default=0,)


class EventTrace(models.Model):

    event_trace_id = models.AutoField(primary_key=True,)
    client = models.ForeignKey('network_ui.Client',)
    trace_session_id = models.IntegerField(default=0,)
    event_data = models.TextField()
    message_id = models.IntegerField()


class Coverage(models.Model):

    coverage_id = models.AutoField(primary_key=True,)
    coverage_data = models.TextField()
    test_result = models.ForeignKey('TestResult',)


class TopologySnapshot(models.Model):

    topology_snapshot_id = models.AutoField(primary_key=True,)
    client = models.ForeignKey('network_ui.Client',)
    topology_id = models.IntegerField()
    trace_session_id = models.IntegerField()
    snapshot_data = models.TextField('TopologySnapshot',)
    order = models.IntegerField()


class TestCase(models.Model):

    test_case_id = models.AutoField(primary_key=True,)
    name = models.CharField('TestCase', max_length=200, blank=True)
    test_case_data = models.TextField()


class Result(models.Model):

    result_id = models.AutoField(primary_key=True,)
    name = models.CharField(max_length=20, blank=True)


class CodeUnderTest(models.Model):

    code_under_test_id = models.AutoField('CodeUnderTest', primary_key=True,)
    version_x = models.IntegerField()
    version_y = models.IntegerField()
    version_z = models.IntegerField()
    commits_since = models.IntegerField()
    commit_hash = models.CharField(max_length=40, blank=True)


class TestResult(models.Model):

    test_result_id = models.AutoField(primary_key=True,)
    test_case = models.ForeignKey('TestCase',)
    result = models.ForeignKey('Result',)
    code_under_test = models.ForeignKey('CodeUnderTest',)
    time = models.DateTimeField()
    id = models.IntegerField(default=0,)
    client = models.ForeignKey('network_ui.Client',)
