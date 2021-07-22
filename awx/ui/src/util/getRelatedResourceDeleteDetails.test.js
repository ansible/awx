import {
  InventoriesAPI,
  InventorySourcesAPI,
  JobTemplatesAPI,
  ProjectsAPI,
  WorkflowJobTemplatesAPI,
  WorkflowJobTemplateNodesAPI,
  CredentialsAPI,
  ExecutionEnvironmentsAPI,
  CredentialInputSourcesAPI,
} from 'api';
import {
  getRelatedResourceDeleteCounts,
  relatedResourceDeleteRequests,
} from './getRelatedResourceDeleteDetails';

jest.mock('../api/models/Credentials');
jest.mock('../api/models/Inventories');
jest.mock('../api/models/InventorySources');
jest.mock('../api/models/JobTemplates');
jest.mock('../api/models/Projects');
jest.mock('../api/models/WorkflowJobTemplates');
jest.mock('../api/models/WorkflowJobTemplateNodes');
jest.mock('../api/models/CredentialInputSources');
jest.mock('../api/models/ExecutionEnvironments');
jest.mock('../api/models/Applications');
jest.mock('../api/models/NotificationTemplates');
jest.mock('../api/models/Teams');

describe('delete details', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should call api for credentials list', () => {
    getRelatedResourceDeleteCounts(
      relatedResourceDeleteRequests.credential({ id: 1 })
    );
    expect(InventorySourcesAPI.read).toBeCalledWith({
      credentials__id: 1,
    });
    expect(JobTemplatesAPI.read).toBeCalledWith({ credentials: 1 });
    expect(ProjectsAPI.read).toBeCalledWith({ credentials: 1 });
  });

  test('should call api for projects list', () => {
    getRelatedResourceDeleteCounts(
      relatedResourceDeleteRequests.project({ id: 1 })
    );
    expect(WorkflowJobTemplateNodesAPI.read).toBeCalledWith({
      unified_job_template: 1,
    });
    expect(InventorySourcesAPI.read).toBeCalledWith({
      source_project: 1,
    });
    expect(JobTemplatesAPI.read).toBeCalledWith({ project: 1 });
  });

  test('should call api for templates list', () => {
    getRelatedResourceDeleteCounts(
      relatedResourceDeleteRequests.template({ id: 1 })
    );
    expect(WorkflowJobTemplateNodesAPI.read).toBeCalledWith({
      unified_job_template: 1,
    });
  });

  test('should call api for credential type list', () => {
    getRelatedResourceDeleteCounts(
      relatedResourceDeleteRequests.credentialType({ id: 1 })
    );
    expect(CredentialsAPI.read).toBeCalledWith({
      credential_type__id: 1,
    });
  });

  test('should call api for inventory list', () => {
    getRelatedResourceDeleteCounts(
      relatedResourceDeleteRequests.inventory({ id: 1 })
    );
    expect(JobTemplatesAPI.read).toBeCalledWith({ inventory: 1 });
    expect(WorkflowJobTemplatesAPI.read).toBeCalledWith({
      inventory: 1,
    });
  });

  test('should call api for inventory source list', async () => {
    InventoriesAPI.updateSources.mockResolvedValue({
      data: [{ inventory_source: 2 }],
    });
    await getRelatedResourceDeleteCounts(
      relatedResourceDeleteRequests.inventorySource(1)
    );
    expect(WorkflowJobTemplateNodesAPI.read).toBeCalledWith({
      unified_job_template: 1,
    });
  });

  test('should call api for organization list', async () => {
    getRelatedResourceDeleteCounts(
      relatedResourceDeleteRequests.organization({ id: 1 })
    );
    expect(CredentialsAPI.read).toBeCalledWith({ organization: 1 });
  });

  test('should call return error for inventory source list', async () => {
    WorkflowJobTemplateNodesAPI.read.mockRejectedValue({
      response: {
        config: {
          method: 'get',
          url: '/api/v2/workflow_job_template_nodes',
        },
        data: 'An error occurred',
        status: 403,
      },
    });
    const { error } = await getRelatedResourceDeleteCounts(
      relatedResourceDeleteRequests.inventorySource(1)
    );

    expect(error).toBeDefined();
  });

  test('should return proper results', async () => {
    JobTemplatesAPI.read.mockResolvedValue({ data: { count: 1 } });
    InventorySourcesAPI.read.mockResolvedValue({ data: { count: 10 } });
    CredentialInputSourcesAPI.read.mockResolvedValue({ data: { count: 20 } });
    ExecutionEnvironmentsAPI.read.mockResolvedValue({ data: { count: 30 } });
    ProjectsAPI.read.mockResolvedValue({ data: { count: 2 } });

    const { results } = await getRelatedResourceDeleteCounts(
      relatedResourceDeleteRequests.credential({ id: 1 })
    );
    expect(results).toEqual({
      'Job Templates': 1,
      Projects: 2,
      'Inventory Sources': 10,
      'Credential Input Sources': 20,
      'Execution Environments': 30,
    });
  });
});
