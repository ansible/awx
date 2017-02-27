# AWX
from awx.main.models import (
    WorkflowJobTemplateNode,
    WorkflowJobTemplate,
)
from awx.main.models.jobs import JobTemplate


def do_init_workflow(job_template_success, job_template_fail, job_template_never, jts_parallel):
    wfjt, created = WorkflowJobTemplate.objects.get_or_create(name="parallel workflow")
    wfjt.delete()
    wfjt, created = WorkflowJobTemplate.objects.get_or_create(name="parallel workflow")
    print(wfjt.id)
    WorkflowJobTemplateNode.objects.all().delete()
    if created:
        node_success = WorkflowJobTemplateNode.objects.create(workflow_job_template=wfjt, unified_job_template=job_template_success)

    nodes_never = []
    for x in range(0, 3):
        nodes_never.append(WorkflowJobTemplateNode.objects.create(workflow_job_template=wfjt, unified_job_template=job_template_never))
    
    nodes_parallel = []
    for jt in jts_parallel:
        nodes_parallel.append(WorkflowJobTemplateNode.objects.create(workflow_job_template=wfjt, unified_job_template=jt))
        
    node_success.success_nodes.add(nodes_parallel[0])
    node_success.success_nodes.add(nodes_parallel[1])
    node_success.success_nodes.add(nodes_parallel[2])

    # Add a failure node for each paralell node
    for i, n in enumerate(nodes_parallel):
        n.failure_nodes.add(nodes_never[i])


def do_init():
    jt_success = JobTemplate.objects.get(id=5)
    jt_fail= JobTemplate.objects.get(id=6)
    jt_never= JobTemplate.objects.get(id=7)
    
    jt_parallel = []
    jt_parallel.append(JobTemplate.objects.get(id=16))
    jt_parallel.append(JobTemplate.objects.get(id=17))
    jt_parallel.append(JobTemplate.objects.get(id=18))
    do_init_workflow(jt_success, jt_fail, jt_never, jt_parallel)


if __name__ == "__main__":
    do_init()
