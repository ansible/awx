import { t } from '@lingui/macro';

import {
  UnifiedJobTemplatesAPI,
  CredentialsAPI,
  InventoriesAPI,
  InventorySourcesAPI,
  JobTemplatesAPI,
  ProjectsAPI,
  WorkflowJobTemplateNodesAPI,
  WorkflowJobTemplatesAPI,
  CredentialInputSourcesAPI,
  TeamsAPI,
  NotificationTemplatesAPI,
  ExecutionEnvironmentsAPI,
  ApplicationsAPI,
  OrganizationsAPI,
  InstanceGroupsAPI,
} from 'api';

export async function getRelatedResourceDeleteCounts(requests) {
  const results = {};
  let error = null;
  let hasCount = false;

  try {
    await Promise.all(
      requests.map(async ({ request, label }) => {
        const {
          data: { count },
        } = await request();

        if (count > 0) {
          results[label] = count;
          hasCount = true;
        }
      })
    );
  } catch (err) {
    error = err;
  }

  return {
    results: hasCount && results,
    error,
  };
}

export const relatedResourceDeleteRequests = {
  credential: (selected) => [
    {
      request: () =>
        JobTemplatesAPI.read({
          credentials: selected.id,
        }),
      label: t`Job Templates`,
    },
    {
      request: () => ProjectsAPI.read({ credentials: selected.id }),
      label: t`Projects`,
    },
    {
      request: () =>
        InventorySourcesAPI.read({
          credentials__id: selected.id,
        }),
      label: t`Inventory Sources`,
    },
    {
      request: () =>
        CredentialInputSourcesAPI.read({
          source_credential: selected.id,
        }),
      label: t`Credential Input Sources`,
    },
    {
      request: () =>
        ExecutionEnvironmentsAPI.read({
          credential: selected.id,
        }),
      label: t`Execution Environments`,
    },
  ],

  credentialType: (selected) => [
    {
      request: async () =>
        CredentialsAPI.read({
          credential_type__id: selected.id,
        }),
      label: t`Credentials`,
    },
  ],

  inventory: (selected) => [
    {
      request: async () =>
        JobTemplatesAPI.read({
          inventory: selected.id,
        }),
      label: t`Job Templates`,
    },
    {
      request: () => WorkflowJobTemplatesAPI.read({ inventory: selected.id }),
      label: t`Workflow Job Template`,
    },
  ],

  inventorySource: (inventorySourceId) => [
    {
      request: async () =>
        WorkflowJobTemplateNodesAPI.read({
          unified_job_template: inventorySourceId,
        }),
      label: t`Workflow Job Template Nodes`,
    },
    {
      request: async () => InventorySourcesAPI.readGroups(inventorySourceId),
      label: t`Groups`,
    },
    {
      request: async () => InventorySourcesAPI.readHosts(inventorySourceId),
      label: t`Hosts`,
    },
  ],

  project: (selected) => [
    {
      request: () =>
        JobTemplatesAPI.read({
          project: selected.id,
        }),
      label: t`Job Templates`,
    },
    {
      request: () =>
        WorkflowJobTemplateNodesAPI.read({
          unified_job_template: selected.id,
        }),
      label: t`Workflow Job Templates`,
    },
    {
      request: () =>
        InventorySourcesAPI.read({
          source_project: selected.id,
        }),
      label: t`Inventory Sources`,
    },
  ],

  template: (selected) => [
    {
      request: async () =>
        WorkflowJobTemplateNodesAPI.read({
          unified_job_template: selected.id,
        }),
      label: [t`Workflow Job Template Nodes`],
    },
  ],

  organization: (selected) => [
    {
      request: async () =>
        CredentialsAPI.read({
          organization: selected.id,
        }),
      label: t`Credential`,
    },
    {
      request: async () =>
        TeamsAPI.read({
          organization: selected.id,
        }),
      label: t`Teams`,
    },
    {
      request: async () =>
        NotificationTemplatesAPI.read({
          organization: selected.id,
        }),
      label: t`Notification Templates`,
    },
    {
      request: () =>
        ExecutionEnvironmentsAPI.read({
          organization: selected.id,
        }),
      label: t`Execution Environments`,
    },
    {
      request: async () =>
        ProjectsAPI.read({
          organization: selected.id,
        }),
      label: [t`Projects`],
    },
    {
      request: () =>
        InventoriesAPI.read({
          organization: selected.id,
        }),
      label: t`Inventories`,
    },
    {
      request: () =>
        ApplicationsAPI.read({
          organization: selected.id,
        }),
      label: t`Applications`,
    },
  ],
  executionEnvironment: (selected) => [
    {
      request: async () =>
        UnifiedJobTemplatesAPI.read({
          execution_environment: selected.id,
        }),
      label: [t`Templates`],
    },
    {
      request: async () =>
        ProjectsAPI.read({
          default_environment: selected.id,
        }),
      label: [t`Projects`],
    },
    {
      request: async () =>
        OrganizationsAPI.read({
          default_environment: selected.id,
        }),
      label: [t`Organizations`],
    },
    {
      request: async () => {
        try {
          const {
            data: { results },
          } = await InventorySourcesAPI.read({
            execution_environment: selected.id,
          });

          const responses = await Promise.all(
            results.map((result) =>
              WorkflowJobTemplateNodesAPI.read({
                unified_job_template: result.id,
              })
            )
          );

          const total = responses.reduce(
            ({ data: { count: acc } }, { data: { count: cur } }) => acc + cur,
            { data: { count: 0 } }
          );
          return { data: { count: total } };
        } catch (err) {
          throw new Error(err);
        }
      },
      label: [t`Workflow Job Template Nodes`],
    },
  ],
  instanceGroup: (selected) => [
    {
      request: () => OrganizationsAPI.read({ instance_groups: selected.id }),
      label: t`Organizations`,
    },
    {
      request: () => InventoriesAPI.read({ instance_groups: selected.id }),
      label: t`Inventories`,
    },
    {
      request: () =>
        UnifiedJobTemplatesAPI.read({ instance_groups: selected.id }),
      label: t`Templates`,
    },
  ],

  instance: (selected) => [
    {
      request: () => InstanceGroupsAPI.read({ instances: selected.id }),
      label: t`Instance Groups`,
    },
  ],
};
