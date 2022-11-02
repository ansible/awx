import React from 'react';
import { act } from 'react-dom/test-utils';
import { JobTemplatesAPI, UnifiedJobTemplatesAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';

import RelatedTemplateList from './RelatedTemplateList';

jest.mock('../../api');

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
        delete: false,
      },
    },
  },
];

describe('<TemplateList />', () => {
  let debug;
  beforeEach(() => {
    JobTemplatesAPI.read.mockResolvedValue({
      data: {
        count: mockTemplates.length,
        results: mockTemplates,
      },
    });

    JobTemplatesAPI.readOptions.mockResolvedValue({
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

  test('Templates are retrieved from the api and the components finishes loading', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <RelatedTemplateList searchParams={{ credentials__id: 1 }} />
      );
    });
    expect(JobTemplatesAPI.read).toBeCalledWith({
      credentials__id: 1,
      order_by: 'name',
      page: 1,
      page_size: 20,
    });
    await act(async () => {
      await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    });
    expect(wrapper.find('TemplateListItem').length).toEqual(
      mockTemplates.length
    );
  });

  test('handleSelect is called when a template list item is selected', async () => {
    const wrapper = mountWithContexts(
      <RelatedTemplateList searchParams={{ credentials__id: 1 }} />
    );
    await act(async () => {
      await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    });
    const checkBox = wrapper.find('TemplateListItem').at(1).find('input');

    checkBox.simulate('change', {
      target: {
        id: 2,
        name: 'Job Template 2',
        url: '/templates/job_template/2',
        type: 'job_template',
        summary_fields: { user_capabilities: { delete: true } },
      },
    });

    expect(wrapper.find('TemplateListItem').at(1).prop('isSelected')).toBe(
      true
    );
  });

  test('handleSelectAll is called when a template list item is selected', async () => {
    const wrapper = mountWithContexts(
      <RelatedTemplateList searchParams={{ credentials__id: 1 }} />
    );
    await act(async () => {
      await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
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
    const wrapper = mountWithContexts(
      <RelatedTemplateList searchParams={{ credentials__id: 1 }} />
    );
    await act(async () => {
      await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    });
    const deleteAbleItem = wrapper.find('TemplateListItem').at(0).find('input');
    const nonDeleteAbleItem = wrapper
      .find('TemplateListItem')
      .at(2)
      .find('input');

    deleteAbleItem.simulate('change', {
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
    deleteAbleItem.simulate('change', {
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
    nonDeleteAbleItem.simulate('change', {
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
    const wrapper = mountWithContexts(
      <RelatedTemplateList searchParams={{ credentials__id: 1 }} />
    );
    await act(async () => {
      await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    });
    const jobTemplate = wrapper.find('TemplateListItem').at(1).find('input');

    jobTemplate.simulate('change', {
      target: {
        id: 2,
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
    expect(JobTemplatesAPI.destroy).toBeCalledWith(2);
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
    let wrapper;

    await act(async () => {
      wrapper = mountWithContexts(
        <RelatedTemplateList searchParams={{ credentials__id: 1 }} />
      );
    });
    wrapper.update();
    expect(JobTemplatesAPI.read).toHaveBeenCalledTimes(1);

    await act(async () => {
      wrapper.find('TemplateListItem').at(0).invoke('onSelect')();
    });
    wrapper.update();

    await act(async () => {
      wrapper.find('ToolbarDeleteButton').invoke('onDelete')();
    });
    wrapper.update();

    const modal = wrapper.find('Modal');
    expect(modal).toHaveLength(1);
    expect(modal.prop('title')).toEqual('Error!');
  });

  test('should properly copy template', async () => {
    JobTemplatesAPI.copy.mockResolvedValue({});
    const wrapper = mountWithContexts(
      <RelatedTemplateList searchParams={{ credentials__id: 1 }} />
    );
    await act(async () => {
      await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    });
    await act(async () =>
      wrapper.find('Button[aria-label="Copy"]').prop('onClick')()
    );
    expect(JobTemplatesAPI.copy).toHaveBeenCalled();
  });
});
