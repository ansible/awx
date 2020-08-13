import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../../../../testUtils/enzymeHelpers';
import { WorkflowJobTemplatesAPI } from '../../../../../../api';
import WorkflowJobTemplatesList from './WorkflowJobTemplatesList';

jest.mock('../../../../../../api/models/WorkflowJobTemplates');

const nodeResource = {
  id: 1,
  name: 'Test Workflow Job Template',
  unified_job_type: 'workflow_job',
};
const onUpdateNodeResource = jest.fn();

describe('WorkflowJobTemplatesList', () => {
  let wrapper;
  afterEach(() => {
    wrapper.unmount();
  });
  test('Row selected when nodeResource id matches row id and clicking new row makes expected callback', async () => {
    WorkflowJobTemplatesAPI.read.mockResolvedValueOnce({
      data: {
        count: 2,
        results: [
          {
            id: 1,
            name: 'Test Workflow Job Template',
            type: 'workflow_job_template',
            url: '/api/v2/workflow_job_templates/1',
          },
          {
            id: 2,
            name: 'Test Workflow Job Template 2',
            type: 'workflow_job_template',
            url: '/api/v2/workflow_job_templates/2',
          },
        ],
      },
    });
    WorkflowJobTemplatesAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <WorkflowJobTemplatesList
          nodeResource={nodeResource}
          onUpdateNodeResource={onUpdateNodeResource}
        />
      );
    });
    wrapper.update();
    expect(
      wrapper
        .find('CheckboxListItem[name="Test Workflow Job Template"]')
        .props().isSelected
    ).toBe(true);
    expect(
      wrapper
        .find('CheckboxListItem[name="Test Workflow Job Template 2"]')
        .props().isSelected
    ).toBe(false);
    wrapper
      .find('CheckboxListItem[name="Test Workflow Job Template 2"]')
      .simulate('click');
    expect(onUpdateNodeResource).toHaveBeenCalledWith({
      id: 2,
      name: 'Test Workflow Job Template 2',
      type: 'workflow_job_template',
      url: '/api/v2/workflow_job_templates/2',
    });
  });
  test('Error shown when read() request errors', async () => {
    WorkflowJobTemplatesAPI.read.mockRejectedValue(new Error());
    await act(async () => {
      wrapper = mountWithContexts(
        <WorkflowJobTemplatesList
          nodeResource={nodeResource}
          onUpdateNodeResource={onUpdateNodeResource}
        />
      );
    });
    wrapper.update();
    expect(wrapper.find('ErrorDetail').length).toBe(1);
  });
});
