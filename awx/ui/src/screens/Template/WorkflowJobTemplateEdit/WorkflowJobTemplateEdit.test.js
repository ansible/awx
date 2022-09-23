import React from 'react';
import { Route } from 'react-router-dom';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  WorkflowJobTemplatesAPI,
  OrganizationsAPI,
  LabelsAPI,
  UsersAPI,
  InventoriesAPI,
} from 'api';
import useDebounce from 'hooks/useDebounce';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import WorkflowJobTemplateEdit from './WorkflowJobTemplateEdit';

jest.mock('../../../hooks/useDebounce');
jest.mock('../../../api/models/WorkflowJobTemplates');
jest.mock('../../../api/models/Organizations');
jest.mock('../../../api/models/Labels');
jest.mock('../../../api/models/Users');
jest.mock('../../../api/models/Inventories');

const mockTemplate = {
  id: 6,
  name: 'Foo',
  description: 'Foo description',
  summary_fields: {
    inventory: { id: 1, name: 'Inventory 1' },
    organization: { id: 1, name: 'Organization 1' },
    labels: {
      results: [
        { name: 'Label 1', id: 1 },
        { name: 'Label 2', id: 2 },
      ],
    },
  },
  scm_branch: 'devel',
  limit: '5000',
  variables: '---',
};

describe('<WorkflowJobTemplateEdit/>', () => {
  let wrapper;
  let history;

  beforeEach(async () => {
    LabelsAPI.read = async () => ({
      data: {
        results: [
          { name: 'Label 1', id: 1 },
          { name: 'Label 2', id: 2 },
          { name: 'Label 3', id: 3 },
        ],
      },
    });

    InventoriesAPI.read.mockResolvedValue({
      data: {
        results: [],
        count: 0,
      },
    });
    InventoriesAPI.readOptions.mockResolvedValue({
      data: { actions: { GET: {}, POST: {} } },
    });

    OrganizationsAPI.read.mockResolvedValue({
      data: { results: [{ id: 1, name: 'Default' }], count: 1 },
    });
    OrganizationsAPI.readOptions.mockResolvedValue({
      data: { actions: { GET: {}, POST: {} } },
    });

    UsersAPI.readAdminOfOrganizations.mockResolvedValue({
      data: { count: 1, results: [{ id: 1, name: 'Default' }] },
    });

    useDebounce.mockImplementation((fn) => fn);

    await act(async () => {
      history = createMemoryHistory({
        initialEntries: ['/templates/workflow_job_template/6/edit'],
      });
      wrapper = mountWithContexts(
        <Route
          path="/templates/workflow_job_template/:id/edit"
          component={() => <WorkflowJobTemplateEdit template={mockTemplate} />}
        />,
        {
          context: {
            router: {
              history,
              route: {
                location: history.location,
                match: { params: { id: 6 } },
              },
            },
          },
        }
      );
      await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    });
  });

  test('renders successfully', () => {
    expect(wrapper.find('WorkflowJobTemplateEdit').length).toBe(1);
  });

  test('api is called to properly to save the updated template.', async () => {
    await act(async () => {
      wrapper.find('input#wfjt-name').simulate('change', {
        target: { value: 'Alex', name: 'name' },
      });
      wrapper.find('input#wfjt-limit').simulate('change', {
        target: { value: '5000', name: 'limit' },
      });
      wrapper.find('LabelSelect').find('SelectToggle').simulate('click');
      wrapper.update();
      wrapper.find('input#wfjt-description').simulate('change', {
        target: { value: 'main', name: 'scm_branch' },
      });
      wrapper.find('input#wfjt-description').simulate('change', {
        target: { value: 'Apollo and Athena', name: 'description' },
      });
    });

    wrapper.update();

    await waitForElement(
      wrapper,
      'SelectOption button[aria-label="Label 3"]',
      (el) => el.length > 0
    );
    wrapper.find('input#wfjt-scm-branch').instance().value = 'main';

    act(() => {
      wrapper
        .find('SelectOption')
        .find('button[aria-label="Label 3"]')
        .prop('onClick')();
    });

    wrapper.update();

    act(() =>
      wrapper
        .find('SelectOption')
        .find('button[aria-label="Label 1"]')
        .prop('onClick')()
    );

    wrapper.update();

    await act(async () => {
      wrapper.find('WorkflowJobTemplateForm').invoke('handleSubmit')();
    });

    expect(WorkflowJobTemplatesAPI.update).toHaveBeenCalledWith(6, {
      name: 'Alex',
      description: 'Apollo and Athena',
      skip_tags: '',
      inventory: 1,
      organization: 1,
      scm_branch: 'main',
      limit: '5000',
      extra_vars: '---',
      webhook_credential: null,
      webhook_url: '',
      webhook_service: '',
      allow_simultaneous: false,
      ask_inventory_on_launch: false,
      ask_limit_on_launch: false,
      ask_scm_branch_on_launch: false,
      ask_variables_on_launch: false,
      ask_labels_on_launch: false,
      ask_skip_tags_on_launch: false,
      ask_tags_on_launch: false,
      job_tags: null,
      skip_tags: null,
    });
    wrapper.update();
    await expect(WorkflowJobTemplatesAPI.disassociateLabel).toBeCalledWith(6, {
      name: 'Label 1',
      id: 1,
    });
    wrapper.update();
    await expect(WorkflowJobTemplatesAPI.associateLabel).toBeCalledTimes(1);
  });

  test('handleCancel navigates the user to the /templates', () => {
    act(() => {
      wrapper.find('WorkflowJobTemplateForm').invoke('handleCancel')();
    });
    expect(history.location.pathname).toBe(
      '/templates/workflow_job_template/6/details'
    );
  });

  test('throwing error renders FormSubmitError component', async () => {
    const error = {
      response: {
        config: {
          method: 'patch',
          url: '/api/v2/workflow_job_templates/',
        },
        data: { detail: 'An error occurred' },
      },
    };
    WorkflowJobTemplatesAPI.update.mockRejectedValue(error);
    await act(async () => {
      wrapper.find('Button[aria-label="Save"]').simulate('click');
    });
    expect(WorkflowJobTemplatesAPI.update).toHaveBeenCalled();
    wrapper.update();
    expect(wrapper.find('WorkflowJobTemplateForm').prop('submitError')).toEqual(
      error
    );
  });

  test('system admin can edit a workflow without provide an org', async () => {
    const templateWithoutOrg = {
      id: 6,
      name: 'Foo',
      description: 'Foo description',
      summary_fields: {
        inventory: { id: 1, name: 'Inventory 1' },
        labels: {
          results: [
            { name: 'Label 1', id: 1 },
            { name: 'Label 2', id: 2 },
          ],
        },
      },
      scm_branch: 'devel',
      limit: '5000',
      variables: '---',
    };

    let newWrapper;
    await act(async () => {
      newWrapper = mountWithContexts(
        <WorkflowJobTemplateEdit template={templateWithoutOrg} />,
        {
          context: {
            router: {
              history,
            },
          },
        }
      );
    });
    await waitForElement(newWrapper, 'ContentLoading', (el) => el.length === 0);
    OrganizationsAPI.read.mockRejectedValue({
      response: {
        config: {
          method: 'get',
          url: '/api/v2/organizations/',
        },
        data: { detail: 'An error occurred' },
      },
    });

    WorkflowJobTemplatesAPI.update.mockResolvedValue();

    await act(async () => {
      newWrapper.find('input#wfjt-description').simulate('change', {
        target: { value: 'bar', name: 'description' },
      });
    });

    await act(async () => {
      await newWrapper.find('Button[aria-label="Save"]').simulate('click');
    });
    expect(newWrapper.find('WorkflowJobTemplateForm').length).toBe(1);
    expect(OrganizationsAPI.read).toBeCalled();
    expect(WorkflowJobTemplatesAPI.update).toBeCalledWith(6, {
      allow_simultaneous: false,
      ask_inventory_on_launch: false,
      ask_labels_on_launch: false,
      ask_limit_on_launch: false,
      ask_scm_branch_on_launch: false,
      ask_skip_tags_on_launch: false,
      ask_tags_on_launch: false,
      ask_variables_on_launch: false,
      description: 'bar',
      extra_vars: '---',
      inventory: 1,
      job_tags: null,
      limit: '5000',
      name: 'Foo',
      organization: 1,
      scm_branch: 'devel',
      skip_tags: null,
      webhook_credential: null,
      webhook_service: '',
      webhook_url: '',
    });
    expect(history.location.pathname).toBe(
      '/templates/workflow_job_template/6/details'
    );
  });
});
