import {
  shape,
  exact,
  arrayOf,
  number,
  string,
  bool,
  objectOf,
  oneOf,
  oneOfType,
} from 'prop-types';

export const Role = shape({
  descendent_roles: arrayOf(string),
  role: shape({
    id: number.isRequired,
    name: string.isRequired,
    description: string,
    user_capabilities: shape({
      unattach: bool,
    }).isRequired,
  }),
});

export const AccessRecord = shape({
  id: number.isRequired,
  username: string.isRequired,
  url: string.isRequired,
  email: string,
  first_name: string,
  last_name: string,
  is_superuser: bool,
  is_system_auditor: bool,
  created: string,
  last_login: string,
  ldap_dn: string,
  related: shape({}),
  summary_fields: shape({
    direct_access: arrayOf(Role).isRequired,
    indirect_access: arrayOf(Role).isRequired,
  }).isRequired,
  type: string,
});

export const Application = shape({
  id: number.isRequired,
  name: string.isRequired,
  organization: number,
  summary_fields: shape({
    organization: shape({
      id: number.isRequired,
      name: string.isRequired,
    }),
  }),
});

export const Organization = shape({
  id: number.isRequired,
  name: string.isRequired,
  custom_virtualenv: string, // ?
  description: string,
  max_hosts: number,
  related: shape(),
  summary_fields: shape({
    object_roles: shape(),
  }),
  type: string,
  url: string,
  created: string,
  modified: string,
});

export const QSConfig = shape({
  defaultParams: shape().isRequired,
  namespace: string,
  integerFields: arrayOf(string).isRequired,
});

export const JobTemplate = shape({
  name: string.isRequired,
  description: string,
  inventory: number,
  job_type: oneOf(['run', 'check']),
  playbook: string,
  project: number,
});

export const WorkFlowJobTemplate = shape({
  name: string.isRequired,
  description: string,
  inventory: number,
});

export const Inventory = shape({
  id: number.isRequired,
  name: string,
  description: string,
  groups_with_active_failures: number,
  has_active_failures: bool,
  has_inventory_sources: bool,
  hosts_with_active_failures: number,
  inventory_sources_with_failures: number,
  kind: string,
  organization_id: number,
  total_groups: number,
  total_hosts: number,
  total_inventory_sources: number,
});

export const InventoryScript = shape({
  description: string,
  id: number.isRequired,
  name: string,
});

export const InstanceGroup = shape({
  id: number.isRequired,
  name: string.isRequired,
});

export const Instance = shape({
  id: number.isRequired,
  name: string.isRequired,
});

export const Label = shape({
  id: number.isRequired,
  name: string.isRequired,
});

export const Credential = shape({
  id: number.isRequired,
  name: string.isRequired,
  cloud: bool,
  kind: string,
});

export const Project = shape({
  id: number.isRequired,
  type: oneOf(['project']),
  url: string,
  related: shape(),
  summary_fields: shape({
    organization: Organization,
    credential: Credential,
    last_job: shape({}),
    last_update: shape({}),
    created_by: shape({}),
    modified_by: shape({}),
    object_roles: shape({}),
    user_capabilities: objectOf(bool),
  }),
  created: string,
  name: string.isRequired,
  description: string,
  scm_type: oneOf(['', 'git', 'hg', 'svn', 'archive', 'insights']),
  scm_url: string,
  scm_branch: string,
  scm_refspec: string,
  scm_clean: bool,
  scm_delete_on_update: bool,
  credential: number,
  status: oneOf([
    'new',
    'pending',
    'waiting',
    'running',
    'successful',
    'failed',
    'error',
    'canceled',
    'never updated',
    'ok',
    'missing',
  ]),
  organization: number,
  scm_update_on_launch: bool,
  scm_update_cache_timeout: number,
  allow_override: bool,
  custom_virtualenv: string,
});

export const Job = shape({
  status: string,
  started: string,
  finished: string,
  job_type: string,
  summary_fields: shape({
    job_template: JobTemplate,
    project: Project,
    inventory: Inventory,
    instance_group: InstanceGroup,
    credentials: arrayOf(Credential),
    labels: shape({
      count: number,
      results: arrayOf(Label),
    }),
  }),
  scm_revision: string,
  limit: oneOfType([number, string]),
  verbosity: number,
  execution_mode: string,
  job_slice_number: number,
  job_slice_count: number,
  extra_vars: string,
  artifacts: shape({}),
});

export const Host = shape({
  id: number.isRequired,
  type: oneOf(['host']),
  url: string,
  related: shape(),
  summary_fields: shape({
    inventory: Inventory,
    last_job: Job,
    last_job_host_summary: shape({}),
    created_by: shape({}),
    modified_by: shape({}),
    user_capabilities: objectOf(bool),
    groups: shape({}),
    recent_jobs: arrayOf(Job),
  }),
  created: string,
  modified: string,
  name: string.isRequired,
  description: string,
  inventory: number.isRequired,
  enabled: bool,
  instance_id: string,
  variables: string,
  last_job: number,
  last_job_host_summary: number,
});

export const Team = shape({
  id: number.isRequired,
  name: string.isRequired,
  organization: number,
});

export const Token = shape({
  id: number.isRequired,
  expires: string.isRequired,
  summary_fields: shape({}),
  scope: string.isRequired,
});

export const User = shape({
  id: number.isRequired,
  type: oneOf(['user']),
  url: string,
  related: shape(),
  summary_fields: shape({
    user_capabilities: objectOf(bool),
  }),
  created: string,
  username: string,
  first_name: string,
  last_name: string,
  email: string.isRequired,
  is_superuser: bool,
  is_system_auditor: bool,
  ldap_dn: string,
  last_login: string,
});

// stripped-down User object found in summary_fields (e.g. modified_by)
export const SummaryFieldUser = shape({
  id: number.isRequired,
  username: string.isRequired,
  first_name: string,
  last_name: string,
});

export const Group = shape({
  id: number.isRequired,
  type: oneOf(['group']),
  url: string,
  related: shape({}),
  summary_fields: shape({}),
  created: string,
  modified: string,
  name: string.isRequired,
  description: string,
  inventory: number,
  variables: string,
});

export const SearchColumns = arrayOf(
  exact({
    name: string.isRequired,
    key: string.isRequired,
    isDefault: bool,
    isBoolean: bool,
    booleanLabels: shape({
      true: string.isRequired,
      false: string.isRequired,
    }),
    options: arrayOf(arrayOf(string, string)),
  })
);

export const SortColumns = arrayOf(
  exact({
    name: string.isRequired,
    key: string.isRequired,
  })
);

export const Schedule = shape({
  rrule: string.isRequired,
  id: number.isRequired,
  type: string,
  url: string,
  related: shape({}),
  summary_fields: shape({}),
  created: string,
  modified: string,
  name: string.isRequired,
  description: string,
  extra_data: oneOfType([string, shape({})]),
  inventory: number,
  scm_branch: string,
  job_type: string,
  job_tags: string,
  skip_tags: string,
  limit: string,
  diff_mode: bool,
  verbosity: number,
  unified_job_template: number,
  enabled: bool,
  dtstart: string,
  dtend: string,
  next_run: string,
  timezone: string,
  until: string,
});

export const SurveyQuestion = shape({
  question_name: string,
  question_description: string,
  required: bool,
  type: string,
  variable: string,
  min: number,
  max: number,
  default: string,
  choices: string,
});

export const Survey = shape({
  name: string,
  description: string,
  spec: arrayOf(SurveyQuestion),
});

export const CredentialType = shape({
  id: number.isRequired,
  type: string.isRequired,
  url: string.isRequired,
  related: shape({}),
  summary_fields: shape({}),
  name: string.isRequired,
  description: string,
  kind: string.isRequired,
  namespace: string,
  inputs: shape({}).isRequired,
});

export const NotificationType = oneOf([
  'email',
  'grafana',
  'irc',
  'mattermost',
  'pagerduty',
  'rocketchat',
  'slack',
  'twilio',
  'webhook',
]);

export const NotificationTemplate = shape({
  id: number.isRequired,
  name: string.isRequired,
  description: string,
  url: string.isRequired,
  organization: number.isRequired,
  notification_type: NotificationType,
  summary_fields: shape({
    organization: Organization,
  }),
});
