import React from 'react';
import { Route } from 'react-router-dom';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  WorkflowJobTemplatesAPI,
  OrganizationsAPI,
  LabelsAPI,
} from '../../../api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import WorkflowJobTemplateAdd from './WorkflowJobTemplateAdd';

jest.mock('../../../api/models/WorkflowJobTemplates');
jest.mock('../../../api/models/Organizations');
jest.mock('../../../api/models/Labels');
jest.mock('../../../api/models/Inventories');

describe('<WorkflowJobTemplateAdd/>', () => {
  let wrapper;
  let history;
  const handleSubmit = jest.fn();
  const handleCancel = jest.fn();
  beforeEach(async () => {
    WorkflowJobTemplatesAPI.create.mockResolvedValue({ data: { id: 1 } });
    OrganizationsAPI.read.mockResolvedValue({ data: { results: [{ id: 1 }] } });
    LabelsAPI.read.mockResolvedValue({
      data: {
        results: [
          { name: 'Label 1', id: 1 },
          { name: 'Label 2', id: 2 },
          { name: 'Label 3', id: 3 },
        ],
      },
    });

    await act(async () => {
      history = createMemoryHistory({
        initialEntries: ['/templates/workflow_job_template/add'],
      });
      await act(async () => {
        wrapper = mountWithContexts(
          <Route
            path="/templates/workflow_job_template/add"
            component={() => (
              <WorkflowJobTemplateAdd
                handleSubmit={handleSubmit}
                handleCancel={handleCancel}
              />
            )}
          />,
          {
            context: {
              router: {
                history,
                route: {
                  location: history.location,
                },
              },
            },
          }
        );
      });
    });
  });
  afterEach(async () => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('initially renders successfully', async () => {
    expect(wrapper.length).toBe(1);
  });

  test('calls workflowJobTemplatesAPI with correct information on submit', async () => {
    await act(async () => {
      wrapper.find('input#wfjt-name').simulate('change', {
        target: { value: 'Alex', name: 'name' },
      });

      wrapper
        .find('LabelSelect')
        .find('SelectToggle')
        .simulate('click');
    });

    wrapper.update();

    act(() => {
      wrapper
        .find('SelectOption')
        .find('button[aria-label="Label 3"]')
        .prop('onClick')();
    });

    wrapper.update();
    await act(async () => {
      wrapper.find('form').simulate('submit');
    });
    await expect(WorkflowJobTemplatesAPI.create).toHaveBeenCalledWith({
      name: 'Alex',
      allow_simultaneous: false,
      ask_inventory_on_launch: false,
      ask_limit_on_launch: false,
      ask_scm_branch_on_launch: false,
      ask_variables_on_launch: false,
      description: '',
      extra_vars: '---',
      inventory: undefined,
      limit: '',
      organization: undefined,
      scm_branch: '',
      webhook_credential: undefined,
      webhook_service: '',
      webhook_url: '',
    });

    expect(WorkflowJobTemplatesAPI.associateLabel).toHaveBeenCalledTimes(1);
  });

  test('handleCancel navigates the user to the /templates', async () => {
    await act(async () => {
      await wrapper.find('WorkflowJobTemplateForm').invoke('handleCancel')();
    });
    expect(history.location.pathname).toBe('/templates');
  });

  test('throwing error renders FormSubmitError component', async () => {
    const error = {
      response: {
        config: {
          method: 'post',
          url: '/api/v2/workflow_job_templates/',
        },
        data: { detail: 'An error occurred' },
      },
    };

    WorkflowJobTemplatesAPI.create.mockRejectedValue(error);
    await act(async () => {
      wrapper.find('input#wfjt-name').simulate('change', {
        target: { value: 'Alex', name: 'name' },
      });
    });

    wrapper.update();
    await act(async () => {
      wrapper.find('form').simulate('submit');
    });

    expect(WorkflowJobTemplatesAPI.create).toHaveBeenCalled();
    wrapper.update();
    expect(wrapper.find('WorkflowJobTemplateForm').prop('submitError')).toEqual(
      error
    );
  });

  test('throwing error prevents navigation away from form', async () => {
    OrganizationsAPI.read.mockRejectedValue({
      response: {
        config: {
          method: 'get',
          url: '/api/v2/organizations/',
        },
        data: 'An error occurred',
      },
    });
    WorkflowJobTemplatesAPI.update.mockResolvedValue();

    await act(async () => {
      await wrapper.find('Button[aria-label="Save"]').simulate('click');
    });
    expect(wrapper.find('WorkflowJobTemplateForm').length).toBe(1);
    expect(OrganizationsAPI.read).toBeCalled();
    expect(history.location.pathname).toBe(
      '/templates/workflow_job_template/add'
    );
  });
});
