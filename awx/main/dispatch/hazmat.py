import django

from awx import prepare_env

prepare_env()


django.setup()  # noqa


from ansible_base.rbac.models import DABPermission, ObjectRole, RoleDefinition, RoleEvaluation, RoleEvaluationUUID, RoleTeamAssignment, RoleUserAssignment
from ansible_base.resource_registry.models.resource import Resource, ResourceType
from ansible_base.resource_registry.models.service_identifier import ServiceID
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.models import Session
from django.contrib.sites.models import Site

# Shell Plus Django Imports
from django.core.cache import cache
from django.db import transaction
from django.db.models import Avg, Case, Count, Exists, F, Max, Min, OuterRef, Prefetch, Q, Subquery, Sum, When
from django.urls import reverse
from django.utils import timezone
from flags.models import FlagState

from awx.conf.models import Setting
from awx.main.models.activity_stream import ActivityStream
from awx.main.models.ad_hoc_commands import AdHocCommand
from awx.main.models.credential import Credential, CredentialInputSource, CredentialType
from awx.main.models.events import (
    AdHocCommandEvent,
    InventoryUpdateEvent,
    JobEvent,
    ProjectUpdateEvent,
    SystemJobEvent,
    UnpartitionedAdHocCommandEvent,
    UnpartitionedInventoryUpdateEvent,
    UnpartitionedJobEvent,
    UnpartitionedProjectUpdateEvent,
    UnpartitionedSystemJobEvent,
)
from awx.main.models.execution_environments import ExecutionEnvironment
from awx.main.models.ha import (
    Instance,
    InstanceGroup,
    InstanceLink,
    InventoryInstanceGroupMembership,
    JobLaunchConfigInstanceGroupMembership,
    OrganizationInstanceGroupMembership,
    ScheduleInstanceGroupMembership,
    TowerScheduleState,
    UnifiedJobTemplateInstanceGroupMembership,
    WorkflowJobInstanceGroupMembership,
    WorkflowJobNodeBaseInstanceGroupMembership,
    WorkflowJobTemplateNodeBaseInstanceGroupMembership,
)
from awx.main.models.inventory import (
    CustomInventoryScript,
    Host,
    HostMetric,
    HostMetricSummaryMonthly,
    Inventory,
    InventoryConstructedInventoryMembership,
    InventorySource,
    InventoryUpdate,
    SmartInventoryMembership,
)
from awx.main.models.jobs import Job, JobHostSummary, JobLaunchConfig, JobTemplate, SystemJob, SystemJobTemplate
from awx.main.models.label import Label
from awx.main.models.notifications import Notification, NotificationTemplate
from awx.main.models.organization import Organization, OrganizationGalaxyCredentialMembership, Team, UserSessionMembership
from awx.main.models.projects import Project, ProjectUpdate
from awx.main.models.rbac import Role, RoleAncestorEntry
from awx.main.models.receptor_address import ReceptorAddress
from awx.main.models.schedules import Schedule
from awx.main.models.unified_jobs import UnifiedJob, UnifiedJobDeprecatedStdout, UnifiedJobTemplate
from awx.main.models.workflow import WorkflowApproval, WorkflowApprovalTemplate, WorkflowJob, WorkflowJobNode, WorkflowJobTemplate, WorkflowJobTemplateNode

from django.core.cache import cache as django_cache
from django.db import connection


connection.close()
django_cache.close()
