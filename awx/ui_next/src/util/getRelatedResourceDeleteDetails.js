import { t } from '@lingui/macro';

import {
  CredentialsAPI,
  InventoriesAPI,
  InventorySourcesAPI,
  JobTemplatesAPI,
  ProjectsAPI,
  WorkflowJobTemplateNodesAPI,
  WorkflowJobTemplatesAPI,
} from '../api';

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
  credential: (selected, i18n) => [
    {
      request: () =>
        JobTemplatesAPI.read({
          credentials: selected.id,
        }),
      label: i18n._(t`Job Templates`),
    },
    {
      request: () => ProjectsAPI.read({ credentials: selected.id }),
      label: i18n._(t`Projects`),
    },
    {
      request: () =>
        InventoriesAPI.read({
          insights_credential: selected.id,
        }),
      label: i18n._(t`Inventories`),
    },
    {
      request: () =>
        InventorySourcesAPI.read({
          credentials__id: selected.id,
        }),
      label: i18n._(t`Inventory Sources`),
    },
  ],

  credentialType: (selected, i18n) => [
    {
      request: async () =>
        CredentialsAPI.read({
          credential_type__id: selected.id,
        }),
      label: i18n._(t`Credentials`),
    },
  ],

  inventory: (selected, i18n) => [
    {
      request: async () =>
        JobTemplatesAPI.read({
          inventory: selected.id,
        }),
      label: i18n._(t`Job Templates`),
    },
    {
      request: () => WorkflowJobTemplatesAPI.read({ inventory: selected.id }),
      label: i18n._(t`Workflow Job Template`),
    },
  ],

  inventorySource: (inventoryId, i18n) => [
    {
      request: async () => {
        try {
          const { data } = await InventoriesAPI.updateSources(inventoryId);
          return WorkflowJobTemplateNodesAPI.read({
            unified_job_template: data[0].inventory_source,
          });
        } catch (err) {
          throw new Error(err);
        }
      },
      label: i18n._(t`Workflow Job Template Node`),
    },
  ],

  project: (selected, i18n) => [
    {
      request: () =>
        JobTemplatesAPI.read({
          credentials: selected.id,
        }),
      label: i18n._(t`Job Templates`),
    },
    {
      request: () => WorkflowJobTemplatesAPI.read({ credentials: selected.id }),
      label: i18n._(t`Workflow Job Templates`),
    },
    {
      request: () =>
        InventorySourcesAPI.read({
          credentials__id: selected.id,
        }),
      label: i18n._(t`Inventory Sources`),
    },
  ],

  template: (selected, i18n) => [
    {
      request: async () =>
        WorkflowJobTemplateNodesAPI.read({
          unified_job_template: selected.id,
        }),
      label: [i18n._(t`Workflow Job Template Node`)],
    },
  ],

  organization: (selected, i18n) => [
    {
      request: async () =>
        CredentialsAPI.read({
          organization: selected.id,
        }),
      label: i18n._(t`Credential`),
    },
  ],
};
