import json
import pytest

from awx.main.tests.live.tests.conftest import wait_for_job

from awx.main.models import JobTemplate, WorkflowJobTemplate, WorkflowJobTemplateNode

JT_NAMES = ('artifact-test-first', 'artifact-test-second', 'artifact-test-reader')
WFT_NAMES = ('artifact-test-outer-wf', 'artifact-test-inner-wf')


@pytest.mark.django_db(transaction=True)
def test_nested_workflow_set_stats_precedence(live_tmp_folder, demo_inv, project_factory, default_org):
    """Reproducer for set_stats artifacts from an outer workflow leaking into
    an inner (child) workflow and overriding the inner workflow's own artifacts.

    Outer WF:  [job_first] --success--> [inner_wf]
    Inner WF:  [job_second] --success--> [job_reader]

    job_first sets via set_stats:
        var1: "outer-only"           (only source, should propagate through)
        var2: "should-be-overridden" (will be overridden by job_second)

    job_second sets via set_stats:
        var2: "from-inner"           (should override outer's value)
        var3: "inner-only"           (only source, should be available)

    job_reader runs debug.yml (no set_stats), we inspect its extra_vars:
        var1 should be "outer-only"           - outer artifacts propagate when uncontested
        var2 should be "from-inner"           - inner artifacts override outer (THE BUG)
        var3 should be "inner-only"           - inner-only artifacts propagate normally
    """
    # Clean up resources from prior runs (delete individually for signals)
    for name in WFT_NAMES:
        for wft in WorkflowJobTemplate.objects.filter(name=name):
            wft.delete()
    for name in JT_NAMES:
        for jt in JobTemplate.objects.filter(name=name):
            jt.delete()

    proj = project_factory(scm_url=f'file://{live_tmp_folder}/debug')
    if proj.current_job:
        wait_for_job(proj.current_job)

    # job_first: sets var1 (outer-only) and var2 (to be overridden by inner)
    jt_first = JobTemplate.objects.create(
        name='artifact-test-first',
        project=proj,
        playbook='set_stats.yml',
        inventory=demo_inv,
        extra_vars=json.dumps({'stats_data': {'var1': 'outer-only', 'var2': 'should-be-overridden'}}),
    )
    # job_second: overrides var2, introduces var3
    jt_second = JobTemplate.objects.create(
        name='artifact-test-second',
        project=proj,
        playbook='set_stats.yml',
        inventory=demo_inv,
        extra_vars=json.dumps({'stats_data': {'var2': 'from-inner', 'var3': 'inner-only'}}),
    )
    # job_reader: just runs, we check what extra_vars it receives
    jt_reader = JobTemplate.objects.create(
        name='artifact-test-reader',
        project=proj,
        playbook='debug.yml',
        inventory=demo_inv,
    )

    # Inner WFT: job_second -> job_reader
    inner_wft = WorkflowJobTemplate.objects.create(name='artifact-test-inner-wf', organization=default_org)
    inner_node_1 = WorkflowJobTemplateNode.objects.create(
        workflow_job_template=inner_wft,
        unified_job_template=jt_second,
        identifier='second',
    )
    inner_node_2 = WorkflowJobTemplateNode.objects.create(
        workflow_job_template=inner_wft,
        unified_job_template=jt_reader,
        identifier='reader',
    )
    inner_node_1.success_nodes.add(inner_node_2)

    # Outer WFT: job_first -> inner_wf
    outer_wft = WorkflowJobTemplate.objects.create(name='artifact-test-outer-wf', organization=default_org)
    outer_node_1 = WorkflowJobTemplateNode.objects.create(
        workflow_job_template=outer_wft,
        unified_job_template=jt_first,
        identifier='first',
    )
    outer_node_2 = WorkflowJobTemplateNode.objects.create(
        workflow_job_template=outer_wft,
        unified_job_template=inner_wft,
        identifier='inner',
    )
    outer_node_1.success_nodes.add(outer_node_2)

    # Launch and wait
    outer_wfj = outer_wft.create_unified_job()
    outer_wfj.signal_start()
    wait_for_job(outer_wfj, running_timeout=120)

    # Find the reader job inside the inner workflow
    inner_wf_node = outer_wfj.workflow_job_nodes.get(identifier='inner')
    inner_wfj = inner_wf_node.job
    assert inner_wfj is not None, 'Inner workflow job was never created'

    # Check that root node of inner WF (job_second) received outer artifacts
    second_node = inner_wfj.workflow_job_nodes.get(identifier='second')
    assert second_node.job is not None, 'Second job was never created'
    second_extra_vars = json.loads(second_node.job.extra_vars)
    assert second_extra_vars.get('var1') == 'outer-only', (
        f'Root node var1: expected "outer-only" (outer artifact should be available to root node), '
        f'got "{second_extra_vars.get("var1")}". '
        f'Outer artifacts are not reaching root nodes of child workflows.'
    )

    reader_node = inner_wfj.workflow_job_nodes.get(identifier='reader')
    assert reader_node.job is not None, 'Reader job was never created'

    reader_extra_vars = json.loads(reader_node.job.extra_vars)

    # var1: only set by outer job_first, no conflict — should propagate through
    assert reader_extra_vars.get('var1') == 'outer-only', f'var1: expected "outer-only" (uncontested outer artifact), ' f'got "{reader_extra_vars.get("var1")}"'

    # var2: set by outer as "should-be-overridden", then by inner as "from-inner"
    # Inner workflow's own ancestor artifacts should take precedence
    assert reader_extra_vars.get('var2') == 'from-inner', (
        f'var2: expected "from-inner" (inner workflow artifact should override outer), '
        f'got "{reader_extra_vars.get("var2")}". '
        f'Outer workflow artifacts are leaking via wj_special_vars. '
        f'reader node ancestor_artifacts={reader_node.ancestor_artifacts}'
    )

    # var3: only set by inner job_second — should propagate normally
    assert reader_extra_vars.get('var3') == 'inner-only', f'var3: expected "inner-only" (inner-only artifact), ' f'got "{reader_extra_vars.get("var3")}"'


@pytest.mark.django_db(transaction=True)
def test_workflow_extra_vars_override_artifacts(live_tmp_folder, demo_inv, project_factory, default_org):
    """Workflow extra_vars should take precedence over set_stats artifacts
    within a single (non-nested) workflow.

    WF (extra_vars: my_var="from-wf-extra-vars"):
        [job_setter] --success--> [job_reader]

    job_setter sets my_var="from-set-stats" via set_stats
    job_reader should see my_var="from-wf-extra-vars" because workflow
    extra_vars are higher precedence than ancestor artifacts.
    """
    wft_name = 'artifact-test-wf-extra-vars-precedence'
    jt_names = ('artifact-test-setter', 'artifact-test-checker')

    for wft in WorkflowJobTemplate.objects.filter(name=wft_name):
        wft.delete()
    for name in jt_names:
        for jt in JobTemplate.objects.filter(name=name):
            jt.delete()

    proj = project_factory(scm_url=f'file://{live_tmp_folder}/debug')
    if proj.current_job:
        wait_for_job(proj.current_job)

    jt_setter = JobTemplate.objects.create(
        name='artifact-test-setter',
        project=proj,
        playbook='set_stats.yml',
        inventory=demo_inv,
        extra_vars=json.dumps({'stats_data': {'my_var': 'from-set-stats'}}),
    )
    jt_checker = JobTemplate.objects.create(
        name='artifact-test-checker',
        project=proj,
        playbook='debug.yml',
        inventory=demo_inv,
    )

    wft = WorkflowJobTemplate.objects.create(
        name=wft_name,
        organization=default_org,
        extra_vars=json.dumps({'my_var': 'from-wf-extra-vars'}),
    )
    node_1 = WorkflowJobTemplateNode.objects.create(
        workflow_job_template=wft,
        unified_job_template=jt_setter,
        identifier='setter',
    )
    node_2 = WorkflowJobTemplateNode.objects.create(
        workflow_job_template=wft,
        unified_job_template=jt_checker,
        identifier='checker',
    )
    node_1.success_nodes.add(node_2)

    wfj = wft.create_unified_job()
    wfj.signal_start()
    wait_for_job(wfj, running_timeout=120)

    checker_node = wfj.workflow_job_nodes.get(identifier='checker')
    assert checker_node.job is not None, 'Checker job was never created'

    checker_extra_vars = json.loads(checker_node.job.extra_vars)
    assert checker_extra_vars.get('my_var') == 'from-wf-extra-vars', (
        f'Expected my_var="from-wf-extra-vars" (workflow extra_vars should override artifacts), '
        f'got my_var="{checker_extra_vars.get("my_var")}". '
        f'checker node ancestor_artifacts={checker_node.ancestor_artifacts}'
    )
