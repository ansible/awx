import React from 'react';
import {
  JobTemplatesAPI,
  UnifiedJobTemplatesAPI,
  WorkflowJobTemplatesAPI,
} from '@api';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';

import TemplatesList, { _TemplatesList } from './TemplateList';

jest.mock('@api');

const mockTemplates = [
  {
    id: 1,
    name: 'Job Template 1',
    url: '/templates/job_template/1',
    type: 'job_template',
    summary_fields: {
      user_capabilities: {
        delete: true,
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

describe('<TemplatesList />', () => {
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
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('initially renders successfully', () => {
    mountWithContexts(
      <TemplatesList
        match={{ path: '/templates', url: '/templates' }}
        location={{ search: '', pathname: '/templates' }}
      />
    );
  });

  test('Templates are retrieved from the api and the components finishes loading', async done => {
    const loadTemplates = jest.spyOn(_TemplatesList.prototype, 'loadTemplates');
    const wrapper = mountWithContexts(<TemplatesList />);
    await waitForElement(
      wrapper,
      'TemplatesList',
      el => el.state('hasContentLoading') === true
    );
    expect(loadTemplates).toHaveBeenCalled();
    await waitForElement(
      wrapper,
      'TemplatesList',
      el => el.state('hasContentLoading') === false
    );
    done();
  });

  test('handleSelect is called when a template list item is selected', async done => {
    const handleSelect = jest.spyOn(_TemplatesList.prototype, 'handleSelect');
    const wrapper = mountWithContexts(<TemplatesList />);
    await waitForElement(
      wrapper,
      'TemplatesList',
      el => el.state('hasContentLoading') === false
    );
    await wrapper
      .find('input#select-jobTemplate-1')
      .closest('DataListCheck')
      .props()
      .onChange();
    expect(handleSelect).toBeCalled();
    await waitForElement(
      wrapper,
      'TemplatesList',
      el => el.state('selected').length === 1
    );
    done();
  });

  test('handleSelectAll is called when a template list item is selected', async done => {
    const handleSelectAll = jest.spyOn(
      _TemplatesList.prototype,
      'handleSelectAll'
    );
    const wrapper = mountWithContexts(<TemplatesList />);
    await waitForElement(
      wrapper,
      'TemplatesList',
      el => el.state('hasContentLoading') === false
    );
    wrapper
      .find('Checkbox#select-all')
      .props()
      .onChange(true);
    expect(handleSelectAll).toBeCalled();
    await waitForElement(
      wrapper,
      'TemplatesList',
      el => el.state('selected').length === 5
    );
    done();
  });

  test('delete button is disabled if user does not have delete capabilities on a selected template', async done => {
    const wrapper = mountWithContexts(<TemplatesList />);
    wrapper.find('TemplatesList').setState({
      templates: mockTemplates,
      itemCount: 5,
      isInitialized: true,
      selected: mockTemplates.slice(0, 4),
    });
    await waitForElement(
      wrapper,
      'ToolbarDeleteButton * button',
      el => el.getDOMNode().disabled === false
    );
    wrapper.find('TemplatesList').setState({
      selected: mockTemplates,
    });
    await waitForElement(
      wrapper,
      'ToolbarDeleteButton * button',
      el => el.getDOMNode().disabled === true
    );
    done();
  });

  test('api is called to delete templates for each selected template.', () => {
    JobTemplatesAPI.destroy = jest.fn();
    WorkflowJobTemplatesAPI.destroy = jest.fn();
    const wrapper = mountWithContexts(<TemplatesList />);
    wrapper.find('TemplatesList').setState({
      templates: mockTemplates,
      itemCount: 5,
      isInitialized: true,
      isModalOpen: true,
      selected: mockTemplates.slice(0, 4),
    });
    wrapper.find('ToolbarDeleteButton').prop('onDelete')();
    expect(JobTemplatesAPI.destroy).toHaveBeenCalledTimes(3);
    expect(WorkflowJobTemplatesAPI.destroy).toHaveBeenCalledTimes(1);
  });

  test('error is shown when template not successfully deleted from api', async done => {
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
    const wrapper = mountWithContexts(<TemplatesList />);
    wrapper.find('TemplatesList').setState({
      templates: mockTemplates,
      itemCount: 1,
      isInitialized: true,
      isModalOpen: true,
      selected: mockTemplates.slice(0, 1),
    });
    wrapper.find('ToolbarDeleteButton').prop('onDelete')();
    await waitForElement(
      wrapper,
      'Modal',
      el => el.props().isOpen === true && el.props().title === 'Error!'
    );

    done();
  });
});
