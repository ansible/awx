import { t } from '@lingui/macro';
import {
  JobTemplatesAPI,
  WorkflowJobTemplatesAPI,
  CredentialsAPI,
  InventoriesAPI,
  ProjectsAPI,
  OrganizationsAPI,
} from '../../api';

export default function getResourceAccessConfig(i18n) {
  return [
    {
      selectedResource: 'jobTemplate',
      label: i18n._(t`Job templates`),
      searchColumns: [
        {
          name: i18n._(t`Name`),
          key: 'name__icontains',
          isDefault: true,
        },
        {
          name: i18n._(t`Playbook name`),
          key: 'playbook__icontains',
        },
        {
          name: i18n._(t`Created By (Username)`),
          key: 'created_by__username__icontains',
        },
        {
          name: i18n._(t`Modified By (Username)`),
          key: 'modified_by__username__icontains',
        },
      ],
      sortColumns: [
        {
          name: i18n._(t`Name`),
          key: 'name',
        },
      ],
      fetchItems: queryParams => JobTemplatesAPI.read(queryParams),
      fetchOptions: () => JobTemplatesAPI.readOptions(),
    },
    {
      selectedResource: 'workflowJobTemplate',
      label: i18n._(t`Workflow job templates`),
      searchColumns: [
        {
          name: i18n._(t`Name`),
          key: 'name__icontains',
          isDefault: true,
        },
        {
          name: i18n._(t`Playbook name`),
          key: 'playbook__icontains',
        },
        {
          name: i18n._(t`Created By (Username)`),
          key: 'created_by__username__icontains',
        },
        {
          name: i18n._(t`Modified By (Username)`),
          key: 'modified_by__username__icontains',
        },
      ],
      sortColumns: [
        {
          name: i18n._(t`Name`),
          key: 'name',
        },
      ],
      fetchItems: queryParams => WorkflowJobTemplatesAPI.read(queryParams),
      fetchOptions: () => WorkflowJobTemplatesAPI.readOptions(),
    },
    {
      selectedResource: 'credential',
      label: i18n._(t`Credentials`),
      searchColumns: [
        {
          name: i18n._(t`Name`),
          key: 'name__icontains',
          isDefault: true,
        },
        {
          name: i18n._(t`Type`),
          key: 'or__scm_type',
          options: [
            [``, i18n._(t`Manual`)],
            [`git`, i18n._(t`Git`)],
            [`hg`, i18n._(t`Mercurial`)],
            [`svn`, i18n._(t`Subversion`)],
            [`archive`, i18n._(t`Remote Archive`)],
            [`insights`, i18n._(t`Red Hat Insights`)],
          ],
        },
        {
          name: i18n._(t`Source Control URL`),
          key: 'scm_url__icontains',
        },
        {
          name: i18n._(t`Modified By (Username)`),
          key: 'modified_by__username__icontains',
        },
        {
          name: i18n._(t`Created By (Username)`),
          key: 'created_by__username__icontains',
        },
      ],
      sortColumns: [
        {
          name: i18n._(t`Name`),
          key: 'name',
        },
      ],
      fetchItems: queryParams => CredentialsAPI.read(queryParams),
      fetchOptions: () => CredentialsAPI.readOptions(),
    },
    {
      selectedResource: 'inventory',
      label: i18n._(t`Inventories`),
      searchColumns: [
        {
          name: i18n._(t`Name`),
          key: 'name__icontains',
          isDefault: true,
        },
        {
          name: i18n._(t`Created By (Username)`),
          key: 'created_by__username__icontains',
        },
        {
          name: i18n._(t`Modified By (Username)`),
          key: 'modified_by__username__icontains',
        },
      ],
      sortColumns: [
        {
          name: i18n._(t`Name`),
          key: 'name',
        },
      ],
      fetchItems: queryParams => InventoriesAPI.read(queryParams),
      fetchOptions: () => InventoriesAPI.readOptions(),
    },
    {
      selectedResource: 'project',
      label: i18n._(t`Projects`),
      searchColumns: [
        {
          name: i18n._(t`Name`),
          key: 'name__icontains',
          isDefault: true,
        },
        {
          name: i18n._(t`Type`),
          key: 'or__scm_type',
          options: [
            [``, i18n._(t`Manual`)],
            [`git`, i18n._(t`Git`)],
            [`hg`, i18n._(t`Mercurial`)],
            [`svn`, i18n._(t`Subversion`)],
            [`archive`, i18n._(t`Remote Archive`)],
            [`insights`, i18n._(t`Red Hat Insights`)],
          ],
        },
        {
          name: i18n._(t`Source Control URL`),
          key: 'scm_url__icontains',
        },
        {
          name: i18n._(t`Modified By (Username)`),
          key: 'modified_by__username__icontains',
        },
        {
          name: i18n._(t`Created By (Username)`),
          key: 'created_by__username__icontains',
        },
      ],
      sortColumns: [
        {
          name: i18n._(t`Name`),
          key: 'name',
        },
      ],
      fetchItems: queryParams => ProjectsAPI.read(queryParams),
      fetchOptions: () => ProjectsAPI.readOptions(),
    },
    {
      selectedResource: 'organization',
      label: i18n._(t`Organizations`),
      searchColumns: [
        {
          name: i18n._(t`Name`),
          key: 'name__icontains',
          isDefault: true,
        },
        {
          name: i18n._(t`Created By (Username)`),
          key: 'created_by__username__icontains',
        },
        {
          name: i18n._(t`Modified By (Username)`),
          key: 'modified_by__username__icontains',
        },
      ],
      sortColumns: [
        {
          name: i18n._(t`Name`),
          key: 'name',
        },
      ],
      fetchItems: queryParams => OrganizationsAPI.read(queryParams),
      fetchOptions: () => OrganizationsAPI.readOptions(),
    },
  ];
}
