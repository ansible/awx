import pytest

from awx.main.access import ScheduleAccess, WorkflowJobTemplateNodeAccess
from awx.main.models import (
    Credential,
    CredentialType,
    InstanceGroup,
    Schedule,
)


@pytest.mark.django_db
class TestWorkflowJobTemplateNodeInstanceGroupAttach:
    """Verify that attaching/unattaching instance_groups to a WFJT node
    requires use_role (not just read access) on the InstanceGroup."""

    def test_read_only_ig_rejected_attach(self, wfjt_node, job_template, rando):
        """A user who can change the node but only has read_role on the IG
        must be denied can_attach for instance_groups."""
        wfjt = wfjt_node.workflow_job_template
        wfjt.admin_role.members.add(rando)
        job_template.execute_role.members.add(rando)

        ig = InstanceGroup.objects.create(name='node-read-only-ig')
        ig.read_role.members.add(rando)

        access = WorkflowJobTemplateNodeAccess(rando)
        assert access.can_change(wfjt_node, None)
        assert not access.can_attach(wfjt_node, ig, 'instance_groups', {})

    def test_read_only_ig_rejected_unattach(self, wfjt_node, job_template, rando):
        """A user who can change the node but only has read_role on the IG
        must be denied can_unattach for instance_groups."""
        wfjt = wfjt_node.workflow_job_template
        wfjt.admin_role.members.add(rando)
        job_template.execute_role.members.add(rando)

        ig = InstanceGroup.objects.create(name='node-ro-unattach-ig')
        ig.read_role.members.add(rando)

        access = WorkflowJobTemplateNodeAccess(rando)
        assert not access.can_unattach(wfjt_node, ig, 'instance_groups')

    def test_use_role_ig_permitted_attach(self, wfjt_node, job_template, rando):
        """A user who can change the node and has use_role on the IG
        must be allowed can_attach for instance_groups."""
        wfjt = wfjt_node.workflow_job_template
        wfjt.admin_role.members.add(rando)
        job_template.execute_role.members.add(rando)

        ig = InstanceGroup.objects.create(name='node-use-role-ig')
        ig.use_role.members.add(rando)

        access = WorkflowJobTemplateNodeAccess(rando)
        assert access.can_attach(wfjt_node, ig, 'instance_groups', {})

    def test_use_role_ig_permitted_unattach(self, wfjt_node, job_template, rando):
        """A user who can change the node and has use_role on the IG
        must be allowed can_unattach for instance_groups."""
        wfjt = wfjt_node.workflow_job_template
        wfjt.admin_role.members.add(rando)
        job_template.execute_role.members.add(rando)

        ig = InstanceGroup.objects.create(name='node-ur-unattach-ig')
        ig.use_role.members.add(rando)

        access = WorkflowJobTemplateNodeAccess(rando)
        assert access.can_unattach(wfjt_node, ig, 'instance_groups')


@pytest.mark.django_db
class TestScheduleInstanceGroupAttach:
    """Verify that attaching/unattaching instance_groups to a Schedule
    requires use_role (not just read access) on the InstanceGroup."""

    rrule = 'DTSTART:20151117T050000Z RRULE:FREQ=DAILY;INTERVAL=1;COUNT=1'

    def test_read_only_ig_rejected_attach(self, job_template, rando):
        """A user who can change the schedule but only has read_role on the IG
        must be denied can_attach for instance_groups."""
        job_template.admin_role.members.add(rando)
        schedule = Schedule.objects.create(
            unified_job_template=job_template,
            rrule=self.rrule,
            created_by=rando,
        )

        ig = InstanceGroup.objects.create(name='sched-read-only-ig')
        ig.read_role.members.add(rando)

        access = ScheduleAccess(rando)
        assert access.can_change(schedule, None)
        assert not access.can_attach(schedule, ig, 'instance_groups', {})

    def test_read_only_ig_rejected_unattach(self, job_template, rando):
        """A user who can change the schedule but only has read_role on the IG
        must be denied can_unattach for instance_groups."""
        job_template.admin_role.members.add(rando)
        schedule = Schedule.objects.create(
            unified_job_template=job_template,
            rrule=self.rrule,
            created_by=rando,
        )

        ig = InstanceGroup.objects.create(name='sched-ro-unattach-ig')
        ig.read_role.members.add(rando)

        access = ScheduleAccess(rando)
        assert not access.can_unattach(schedule, ig, 'instance_groups')

    def test_use_role_ig_permitted_attach(self, job_template, rando):
        """A user who can change the schedule and has use_role on the IG
        must be allowed can_attach for instance_groups."""
        job_template.admin_role.members.add(rando)
        schedule = Schedule.objects.create(
            unified_job_template=job_template,
            rrule=self.rrule,
            created_by=rando,
        )

        ig = InstanceGroup.objects.create(name='sched-use-role-ig')
        ig.use_role.members.add(rando)

        access = ScheduleAccess(rando)
        assert access.can_attach(schedule, ig, 'instance_groups', {})

    def test_use_role_ig_permitted_unattach(self, job_template, rando):
        """A user who can change the schedule and has use_role on the IG
        must be allowed can_unattach for instance_groups."""
        job_template.admin_role.members.add(rando)
        schedule = Schedule.objects.create(
            unified_job_template=job_template,
            rrule=self.rrule,
            created_by=rando,
        )

        ig = InstanceGroup.objects.create(name='sched-ur-unattach-ig')
        ig.use_role.members.add(rando)

        access = ScheduleAccess(rando)
        assert access.can_unattach(schedule, ig, 'instance_groups')

    def test_non_ig_attach_falls_through(self, job_template, rando):
        """Attaching a non-instance_groups relationship (credentials) should
        still use the super() fallthrough path."""
        job_template.admin_role.members.add(rando)
        schedule = Schedule.objects.create(
            unified_job_template=job_template,
            rrule=self.rrule,
            created_by=rando,
        )

        ct = CredentialType.objects.create(
            name='test-cred-type',
            kind='cloud',
            inputs={},
            injectors={},
        )
        cred = Credential.objects.create(
            name='test-cred',
            credential_type=ct,
        )
        cred.use_role.members.add(rando)

        access = ScheduleAccess(rando)
        assert access.can_attach(schedule, cred, 'credentials', {})

    def test_non_ig_unattach_falls_through(self, job_template, rando):
        """Unattaching a non-instance_groups relationship (credentials) should
        still use the super() fallthrough path."""
        job_template.admin_role.members.add(rando)
        schedule = Schedule.objects.create(
            unified_job_template=job_template,
            rrule=self.rrule,
            created_by=rando,
        )

        ct = CredentialType.objects.create(
            name='test-cred-type-un',
            kind='cloud',
            inputs={},
            injectors={},
        )
        cred = Credential.objects.create(
            name='test-cred-un',
            credential_type=ct,
        )
        cred.use_role.members.add(rando)

        access = ScheduleAccess(rando)
        assert access.can_unattach(schedule, cred, 'credentials')
