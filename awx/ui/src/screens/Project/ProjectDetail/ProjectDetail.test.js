import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  ProjectsAPI,
  JobTemplatesAPI,
  WorkflowJobTemplatesAPI,
  InventorySourcesAPI,
} from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import ProjectDetail from './ProjectDetail';

jest.mock('../../../api');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useRouteMatch: () => ({
    url: '/projects/1/details',
  }),
}));
jest.mock('hooks/useBrandName', () => ({
  __esModule: true,
  default: () => ({
    current: 'AWX',
  }),
}));
describe('<ProjectDetail />', () => {
  const mockProject = {
    id: 1,
    type: 'project',
    url: '/api/v2/projects/1',
    summary_fields: {
      organization: {
        id: 10,
        name: 'Foo',
      },
      default_environment: {
        id: 12,
        name: 'Bar',
        image: 'quay.io/ansible/awx-ee',
      },
      credential: {
        id: 1000,
        name: 'qux',
        kind: 'scm',
      },
      signature_validation_credential: {
        id: 2000,
        name: 'svc',
        kind: 'cryptography',
      },
      last_job: {
        id: 9000,
        status: 'successful',
      },
      created_by: {
        id: 1,
        username: 'admin',
      },
      modified_by: {
        id: 1,
        username: 'admin',
      },
      user_capabilities: {
        edit: true,
        delete: true,
        start: true,
        schedule: true,
        copy: true,
      },
    },
    created: '2019-10-10T01:15:06.780472Z',
    modified: '2019-10-10T01:15:06.780490Z',
    name: 'Project 1',
    description: 'lorem ipsum',
    scm_type: 'git',
    scm_url: 'https://mock.com/bar',
    scm_branch: 'baz',
    scm_refspec: 'refs/remotes/*',
    scm_clean: true,
    scm_delete_on_update: true,
    scm_track_submodules: true,
    credential: 100,
    signature_validation_credential: 200,
    status: 'successful',
    organization: 10,
    scm_update_on_launch: true,
    scm_update_cache_timeout: 5,
    allow_override: true,
    custom_virtualenv: '/custom-venv',
    default_environment: 1,
  };

  test('initially renders successfully', () => {
    mountWithContexts(<ProjectDetail project={mockProject} />);
  });

  test('should render Details', () => {
    const wrapper = mountWithContexts(<ProjectDetail project={mockProject} />);
    function assertDetail(label, value) {
      expect(wrapper.find(`Detail[label="${label}"] dt`).text()).toBe(label);
      expect(wrapper.find(`Detail[label="${label}"] dd`).text()).toBe(value);
    }
    assertDetail('Name', mockProject.name);
    assertDetail('Description', mockProject.description);
    assertDetail('Organization', mockProject.summary_fields.organization.name);
    assertDetail('Source Control Type', 'Git');
    assertDetail('Source Control URL', mockProject.scm_url);
    assertDetail('Source Control Branch', mockProject.scm_branch);
    assertDetail('Source Control Refspec', mockProject.scm_refspec);
    assertDetail(
      'Source Control Credential',
      `Scm: ${mockProject.summary_fields.credential.name}`
    );
    assertDetail(
      'Content Signature Validation Credential',
      `Cryptography: ${mockProject.summary_fields.signature_validation_credential.name}`
    );
    assertDetail(
      'Cache Timeout',
      `${mockProject.scm_update_cache_timeout} Seconds`
    );
    const executionEnvironment = wrapper.find('ExecutionEnvironmentDetail');
    expect(executionEnvironment).toHaveLength(1);
    expect(executionEnvironment.find('dt').text()).toEqual(
      'Default Execution Environment'
    );
    expect(executionEnvironment.find('dd').text()).toEqual(
      mockProject.summary_fields.default_environment.name
    );

    const dateDetails = wrapper.find('UserDateDetail');
    expect(dateDetails).toHaveLength(2);
    expect(dateDetails.at(0).prop('label')).toEqual('Created');
    expect(dateDetails.at(0).prop('date')).toEqual(
      '2019-10-10T01:15:06.780472Z'
    );
    expect(dateDetails.at(1).prop('label')).toEqual('Last Modified');
    expect(dateDetails.at(1).prop('date')).toEqual(
      '2019-10-10T01:15:06.780490Z'
    );
    expect(
      wrapper.find('Detail[label="Enabled Options"]').find('li')
    ).toHaveLength(5);
    const options = [
      'Discard local changes before syncing',
      'Delete the project before syncing',
      'Track submodules latest commit on branch',
      'Update revision on job launch',
      'Allow branch override',
    ];
    wrapper.find('li').map((item, index) => {
      expect(item.text().includes(options[index]));
    });
  });

  test('should hide options label when all project options return false', () => {
    const mockOptions = {
      scm_type: '',
      scm_clean: false,
      scm_delete_on_update: false,
      scm_track_submodules: false,
      scm_update_on_launch: false,
      allow_override: false,
      created: '',
      modified: '',
    };
    const wrapper = mountWithContexts(
      <ProjectDetail project={{ ...mockProject, ...mockOptions }} />
    );
    expect(wrapper.find('Detail[label="Enabled Options"]').length).toBe(0);
  });

  test('should have proper number of delete detail requests', () => {
    JobTemplatesAPI.read.mockResolvedValue({ data: { count: 0 } });
    WorkflowJobTemplatesAPI.read.mockResolvedValue({ data: { count: 0 } });
    InventorySourcesAPI.read.mockResolvedValue({ data: { count: 0 } });
    const mockOptions = {
      scm_type: '',
      scm_clean: false,
      scm_delete_on_update: false,
      scm_update_on_launch: false,
      allow_override: false,
      created: '',
      modified: '',
    };
    const wrapper = mountWithContexts(
      <ProjectDetail project={{ ...mockProject, ...mockOptions }} />
    );
    expect(
      wrapper.find('DeleteButton').prop('deleteDetailsRequests')
    ).toHaveLength(3);
  });

  test('should render with missing summary fields', async () => {
    const wrapper = mountWithContexts(
      <ProjectDetail project={{ ...mockProject, summary_fields: {} }} />
    );
    await waitForElement(
      wrapper,
      'Detail[label="Name"]',
      (el) => el.length === 1
    );
  });

  test('should show edit and sync button for users with edit permission', async () => {
    const wrapper = mountWithContexts(<ProjectDetail project={mockProject} />);
    const editButton = await waitForElement(
      wrapper,
      'ProjectDetail Button[aria-label="edit"]'
    );

    const syncButton = await waitForElement(
      wrapper,
      'ProjectDetail Button[aria-label="Sync Project"]'
    );
    expect(editButton.text()).toEqual('Edit');
    expect(syncButton.text()).toEqual('Sync');
    expect(editButton.prop('to')).toBe(`/projects/${mockProject.id}/edit`);
  });

  test('should hide edit button for users without edit permission', async () => {
    const wrapper = mountWithContexts(
      <ProjectDetail
        project={{
          ...mockProject,
          summary_fields: {
            user_capabilities: {
              edit: false,
            },
          },
        }}
      />
    );
    await waitForElement(wrapper, 'ProjectDetail');
    expect(wrapper.find('ProjectDetail Button[aria-label="edit"]').length).toBe(
      0
    );
    expect(wrapper.find('ProjectDetail Button[aria-label="sync"]').length).toBe(
      0
    );
  });

  test('edit button should navigate to project edit', () => {
    const history = createMemoryHistory();
    const wrapper = mountWithContexts(<ProjectDetail project={mockProject} />, {
      context: { router: { history } },
    });
    expect(wrapper.find('Button[aria-label="edit"]').length).toBe(1);
    wrapper
      .find('Button[aria-label="edit"] Link')
      .simulate('click', { button: 0 });
    expect(history.location.pathname).toEqual('/projects/1/edit');
  });

  test('sync button should call api to sync project', async () => {
    ProjectsAPI.readSync.mockResolvedValue({ data: { can_update: true } });
    const wrapper = mountWithContexts(<ProjectDetail project={mockProject} />);
    await act(() =>
      wrapper
        .find('ProjectDetail Button[aria-label="Sync Project"]')
        .prop('onClick')(1)
    );
    expect(ProjectsAPI.sync).toHaveBeenCalledTimes(1);
  });

  test('expected api calls are made for delete', async () => {
    const wrapper = mountWithContexts(<ProjectDetail project={mockProject} />);
    await waitForElement(wrapper, 'ProjectDetail Button[aria-label="Delete"]');
    await act(async () => {
      wrapper.find('DeleteButton').invoke('onConfirm')();
    });
    expect(ProjectsAPI.destroy).toHaveBeenCalledTimes(1);
  });

  test('Error dialog shown for failed deletion', async () => {
    ProjectsAPI.destroy.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    const wrapper = mountWithContexts(<ProjectDetail project={mockProject} />);
    await waitForElement(wrapper, 'ProjectDetail Button[aria-label="Delete"]');
    await act(async () => {
      wrapper.find('DeleteButton').invoke('onConfirm')();
    });
    await waitForElement(
      wrapper,
      'Modal[title="Error!"]',
      (el) => el.length === 1
    );
    await act(async () => {
      wrapper.find('Modal[title="Error!"]').invoke('onClose')();
    });
    await waitForElement(
      wrapper,
      'Modal[title="Error!"]',
      (el) => el.length === 0
    );
  });
});
