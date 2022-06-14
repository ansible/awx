import { t } from '@lingui/macro';

/* eslint-disable-next-line import/prefer-default-export */
export const JOB_TYPE_URL_SEGMENTS = {
  job: 'playbook',
  project_update: 'project',
  system_job: 'management',
  inventory_update: 'inventory',
  ad_hoc_command: 'command',
  workflow_job: 'workflow',
};

export const SESSION_TIMEOUT_KEY = 'awx-session-timeout';
export const SESSION_REDIRECT_URL = 'awx-redirect-url';
export const PERSISTENT_FILTER_KEY = 'awx-persistent-filter';
export const SESSION_USER_ID = 'awx-session-user-id';

export const VERBOSITY = {
  0: t`0 (Normal)`,
  1: t`1 (Verbose)`,
  2: t`2 (More Verbose)`,
  3: t`3 (Debug)`,
  4: t`4 (Connection Debug)`,
  5: t`5 (WinRM Debug)`,
};

export const VERBOSE_OPTIONS = Object.entries(VERBOSITY).map(([k, v]) => ({
  key: k,
  value: k,
  label: v,
}));
