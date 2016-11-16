# AWX
from awx.main.models import (
    WorkflowJobTemplateNode,
    WorkflowJobTemplate,
)
from awx.main.models.jobs import JobTemplate


def do_init_workflow(job_template_success, job_template_fail, job_template_never):
    wfjt, created = WorkflowJobTemplate.objects.get_or_create(name="linear workflow")
    wfjt.delete()
    wfjt, created = WorkflowJobTemplate.objects.get_or_create(name="linear workflow")
    print(wfjt.id)
    WorkflowJobTemplateNode.objects.all().delete()
    if created:
        nodes_success = []
        nodes_fail = []
        nodes_never = []
        for i in range(0, 2):
            nodes_success.append(WorkflowJobTemplateNode.objects.create(workflow_job_template=wfjt, unified_job_template=job_template_success))
            nodes_fail.append(WorkflowJobTemplateNode.objects.create(workflow_job_template=wfjt, unified_job_template=job_template_fail))
            nodes_never.append(WorkflowJobTemplateNode.objects.create(workflow_job_template=wfjt, unified_job_template=job_template_never))
        nodes_never.append(WorkflowJobTemplateNode.objects.create(workflow_job_template=wfjt, unified_job_template=job_template_never))
        nodes_fail[1].delete()

        nodes_success[0].success_nodes.add(nodes_fail[0])
        nodes_success[0].failure_nodes.add(nodes_never[0])

        nodes_fail[0].failure_nodes.add(nodes_success[1])
        nodes_fail[0].success_nodes.add(nodes_never[1])
        
        nodes_success[1].failure_nodes.add(nodes_never[2])


def do_init():
    jt_success = JobTemplate.objects.get(id=5)
    jt_fail= JobTemplate.objects.get(id=6)
    jt_never= JobTemplate.objects.get(id=7)
    do_init_workflow(jt_success, jt_fail, jt_never)


if __name__ == "__main__":
    do_init()
