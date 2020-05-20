import { t } from '@lingui/macro';
import {
  JobTemplatesAPI,
  WorkflowJobTemplatesAPI,
  CredentialsAPI,
  InventoriesAPI,
  ProjectsAPI,
  OrganizationsAPI,
} from '../../api';

export default function getResourceTypes(i18n) {
  return [
    {
      selectedResource: 'jobTemplate',
      label: i18n._(t`Job templates`),
      searchColumns: [
        {
          name: i18n._(t`Name`),
          key: 'name',
          isDefault: true,
        },
        {
          name: i18n._(t`Playbook name`),
          key: 'playbook',
        },
        {
          name: i18n._(t`Created By (Username)`),
          key: 'created_by__username',
        },
        {
          name: i18n._(t`Modified By (Username)`),
          key: 'modified_by__username',
        },
      ],
      sortColumns: [
        {
          name: i18n._(t`Name`),
          key: 'name',
        },
      ],
      fetchItems: () => JobTemplatesAPI.read(),
    },
    {
      selectedResource: 'workflowJobTemplate',
      label: i18n._(t`Workflow job templates`),
      searchColumns: [
        {
          name: i18n._(t`Name`),
          key: 'name',
          isDefault: true,
        },
        {
          name: i18n._(t`Playbook name`),
          key: 'playbook',
        },
        {
          name: i18n._(t`Created By (Username)`),
          key: 'created_by__username',
        },
        {
          name: i18n._(t`Modified By (Username)`),
          key: 'modified_by__username',
        },
      ],
      sortColumns: [
        {
          name: i18n._(t`Name`),
          key: 'name',
        },
      ],
      fetchItems: () => WorkflowJobTemplatesAPI.read(),
    },
    {
      selectedResource: 'credential',
      label: i18n._(t`Credentials`),
      searchColumns: [
        {
          name: i18n._(t`Name`),
          key: 'name',
          isDefault: true,
        },
        {
          name: i18n._(t`Type`),
          key: 'scm_type',
          options: [
            [``, i18n._(t`Manual`)],
            [`git`, i18n._(t`Git`)],
            [`hg`, i18n._(t`Mercurial`)],
            [`svn`, i18n._(t`Subversion`)],
            [`insights`, i18n._(t`Red Hat Insights`)],
          ],
        },
        {
          name: i18n._(t`Source Control URL`),
          key: 'scm_url',
        },
        {
          name: i18n._(t`Modified By (Username)`),
          key: 'modified_by__username',
        },
        {
          name: i18n._(t`Created By (Username)`),
          key: 'created_by__username',
        },
      ],
      sortColumns: [
        {
          name: i18n._(t`Name`),
          key: 'name',
        },
      ],
      fetchItems: () => CredentialsAPI.read(),
    },
    {
      selectedResource: 'inventory',
      label: i18n._(t`Inventories`),
      searchColumns: [
        {
          name: i18n._(t`Name`),
          key: 'name',
          isDefault: true,
        },
        {
          name: i18n._(t`Created By (Username)`),
          key: 'created_by__username',
        },
        {
          name: i18n._(t`Modified By (Username)`),
          key: 'modified_by__username',
        },
      ],
      sortColumns: [
        {
          name: i18n._(t`Name`),
          key: 'name',
        },
      ],
      fetchItems: () => InventoriesAPI.read(),
    },
    {
      selectedResource: 'project',
      label: i18n._(t`Projects`),
      searchColumns: [
        {
          name: i18n._(t`Name`),
          key: 'name',
          isDefault: true,
        },
        {
          name: i18n._(t`Type`),
          key: 'scm_type',
          options: [
            [``, i18n._(t`Manual`)],
            [`git`, i18n._(t`Git`)],
            [`hg`, i18n._(t`Mercurial`)],
            [`svn`, i18n._(t`Subversion`)],
            [`insights`, i18n._(t`Red Hat Insights`)],
          ],
        },
        {
          name: i18n._(t`Source Control URL`),
          key: 'scm_url',
        },
        {
          name: i18n._(t`Modified By (Username)`),
          key: 'modified_by__username',
        },
        {
          name: i18n._(t`Created By (Username)`),
          key: 'created_by__username',
        },
      ],
      sortColumns: [
        {
          name: i18n._(t`Name`),
          key: 'name',
        },
      ],
      fetchItems: () => ProjectsAPI.read(),
    },
    {
      selectedResource: 'organization',
      label: i18n._(t`Organizations`),
      searchColumns: [
        {
          name: i18n._(t`Name`),
          key: 'name',
          isDefault: true,
        },
        {
          name: i18n._(t`Created By (Username)`),
          key: 'created_by__username',
        },
        {
          name: i18n._(t`Modified By (Username)`),
          key: 'modified_by__username',
        },
      ],
      sortColumns: [
        {
          name: i18n._(t`Name`),
          key: 'name',
        },
      ],
      fetchItems: () => OrganizationsAPI.read(),
    },
  ];
}
