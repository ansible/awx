import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  JobTemplatesAPI,
  UnifiedJobTemplatesAPI,
  WorkflowJobTemplatesAPI,
} from '../../../api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';

import DashboardTemplateList from './DashboardTemplateList';

jest.mock('../../../api');

const mockTemplates = [
  {
    id: 1,
    name: 'Job Template 1',
    url: '/templates/job_template/1',
    type: 'job_template',
    summary_fields: {
      user_capabilities: {
        delete: true,
        edit: true,
        copy: true,
      },
    },
  },
  {
    id: 2,
    name: 'Job Template 2',
    url: '/templates/job_template/2',
    type: 'job_template',
    summary_fields: {
      user_capabilities: {
        delete: true,
      },
    },
  },
  {
    id: 3,
    name: 'Job Template 3',
    url: '/templates/job_template/3',
    type: 'job_template',
    summary_fields: {
      user_capabilities: {
        delete: true,
      },
    },
  },
  {
    id: 4,
    name: 'Workflow Job Template 1',
    url: '/templates/workflow_job_template/4',
    type: 'workflow_job_template',
    summary_fields: {
      user_capabilities: {
        delete: true,
      },
    },
  },
  {
    id: 5,
    name: 'Workflow Job Template 2',
    url: '/templates/workflow_job_template/5',
    type: 'workflow_job_template',
    summary_fields: {
      user_capabilities: {
        delete: false,
      },
    },
  },
];

describe('<DashboardTemplateList />', () => {
  let debug;
  beforeEach(() => {
    UnifiedJobTemplatesAPI.read.mockResolvedValue({
      data: {
        count: mockTemplates.length,
        results: mockTemplates,
      },
    });

    UnifiedJobTemplatesAPI.readOptions.mockResolvedValue({
      data: {
        actions: [],
      },
    });
    debug = global.console.debug; // eslint-disable-line prefer-destructuring
    global.console.debug = () => {};
  });

  afterEach(() => {
    jest.clearAllMocks();
    global.console.debug = debug;
  });

  test('initially renders successfully', async () => {
    await act(async () => {
      mountWithContexts(
        <DashboardTemplateList
          match={{ path: '/templates', url: '/templates' }}
          location={{ search: '', pathname: '/templates' }}
        />
      );
    });
  });

  test('Templates are retrieved from the api and the components finishes loading', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<DashboardTemplateList />);
    });
    expect(UnifiedJobTemplatesAPI.read).toBeCalled();
    await act(async () => {
      await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    });
    expect(wrapper.find('DashboardTemplateListItem').length).toEqual(5);
  });

  test('handleSelect is called when a template list item is selected', async () => {
    const wrapper = mountWithContexts(<DashboardTemplateList />);
    await act(async () => {
      await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    });
    const checkBox = wrapper
      .find('DashboardTemplateListItem')
      .at(1)
      .find('input');

    checkBox.simulate('change', {
      target: {
        id: 2,
        name: 'Job Template 2',
        url: '/templates/job_template/2',
        type: 'job_template',
        summary_fields: { user_capabilities: { delete: true } },
      },
    });

    expect(
      wrapper
        .find('DashboardTemplateListItem')
        .at(1)
        .prop('isSelected')
    ).toBe(true);
  });

  test('handleSelectAll is called when a template list item is selected', async () => {
    const wrapper = mountWithContexts(<DashboardTemplateList />);
    await act(async () => {
      await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    });
    expect(wrapper.find('Checkbox#select-all').prop('isChecked')).toBe(false);

    const toolBarCheckBox = wrapper.find('Checkbox#select-all');
    act(() => {
      toolBarCheckBox.prop('onChange')(true);
    });
    wrapper.update();
    expect(wrapper.find('Checkbox#select-all').prop('isChecked')).toBe(true);
  });

  test('delete button is disabled if user does not have delete capabilities on a selected template', async () => {
    const wrapper = mountWithContexts(<DashboardTemplateList />);
    await act(async () => {
      await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    });
    const deleteableItem = wrapper
      .find('DashboardTemplateListItem')
      .at(0)
      .find('input');
    const nonDeleteableItem = wrapper
      .find('DashboardTemplateListItem')
      .at(4)
      .find('input');

    deleteableItem.simulate('change', {
      id: 1,
      name: 'Job Template 1',
      url: '/templates/job_template/1',
      type: 'job_template',
      summary_fields: {
        user_capabilities: {
          delete: true,
        },
      },
    });

    expect(wrapper.find('Button[aria-label="Delete"]').prop('isDisabled')).toBe(
      false
    );
    deleteableItem.simulate('change', {
      id: 1,
      name: 'Job Template 1',
      url: '/templates/job_template/1',
      type: 'job_template',
      summary_fields: {
        user_capabilities: {
          delete: true,
        },
      },
    });
    expect(wrapper.find('Button[aria-label="Delete"]').prop('isDisabled')).toBe(
      true
    );
    nonDeleteableItem.simulate('change', {
      id: 5,
      name: 'Workflow Job Template 2',
      url: '/templates/workflow_job_template/5',
      type: 'workflow_job_template',
      summary_fields: {
        user_capabilities: {
          delete: false,
        },
      },
    });
    expect(wrapper.find('Button[aria-label="Delete"]').prop('isDisabled')).toBe(
      true
    );
  });

  test('api is called to delete templates for each selected template.', async () => {
    const wrapper = mountWithContexts(<DashboardTemplateList />);
    await act(async () => {
      await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    });
    const jobTemplate = wrapper
      .find('DashboardTemplateListItem')
      .at(1)
      .find('input');
    const workflowJobTemplate = wrapper
      .find('DashboardTemplateListItem')
      .at(3)
      .find('input');

    jobTemplate.simulate('change', {
      target: {
        id: 2,
        name: 'Job Template 2',
        url: '/templates/job_template/2',
        type: 'job_template',
        summary_fields: { user_capabilities: { delete: true } },
      },
    });

    workflowJobTemplate.simulate('change', {
      target: {
        id: 4,
        name: 'Workflow Job Template 1',
        url: '/templates/workflow_job_template/4',
        type: 'workflow_job_template',
        summary_fields: {
          user_capabilities: {
            delete: true,
          },
        },
      },
    });

    await act(async () => {
      wrapper.find('button[aria-label="Delete"]').prop('onClick')();
    });
    wrapper.update();
    await act(async () => {
      await wrapper
        .find('button[aria-label="confirm delete"]')
        .prop('onClick')();
    });
    expect(JobTemplatesAPI.destroy).toBeCalledWith(2);
    expect(WorkflowJobTemplatesAPI.destroy).toBeCalledWith(4);
  });

  test('error is shown when template not successfully deleted from api', async () => {
    JobTemplatesAPI.destroy.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'delete',
            url: '/api/v2/job_templates/1',
          },
          data: 'An error occurred',
        },
      })
    );
    const wrapper = mountWithContexts(<DashboardTemplateList />);
    await act(async () => {
      await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    });
    const checkBox = wrapper
      .find('DashboardTemplateListItem')
      .at(1)
      .find('input');

    checkBox.simulate('change', {
      target: {
        id: 'a',
        name: 'Job Template 2',
        url: '/templates/job_template/2',
        type: 'job_template',
        summary_fields: { user_capabilities: { delete: true } },
      },
    });
    await act(async () => {
      wrapper.find('button[aria-label="Delete"]').prop('onClick')();
    });
    wrapper.update();
    await act(async () => {
      await wrapper
        .find('button[aria-label="confirm delete"]')
        .prop('onClick')();
    });

    await waitForElement(
      wrapper,
      'Modal[aria-label="Deletion Error"]',
      el => el.props().isOpen === true && el.props().title === 'Error!'
    );
  });
  test('should properly copy template', async () => {
    JobTemplatesAPI.copy.mockResolvedValue({});
    const wrapper = mountWithContexts(<DashboardTemplateList />);
    await act(async () => {
      await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    });
    await act(async () =>
      wrapper.find('Button[aria-label="Copy"]').prop('onClick')()
    );
    expect(JobTemplatesAPI.copy).toHaveBeenCalled();
    expect(UnifiedJobTemplatesAPI.read).toHaveBeenCalled();
    wrapper.update();
  });
});
