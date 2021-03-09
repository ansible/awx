import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../../../../testUtils/enzymeHelpers';
import { JobTemplatesAPI } from '../../../../../../api';
import JobTemplatesList from './JobTemplatesList';

jest.mock('../../../../../../api/models/JobTemplates');

const nodeResource = {
  id: 1,
  name: 'Test Job Template',
  unified_job_type: 'job',
};
const onUpdateNodeResource = jest.fn();

describe('JobTemplatesList', () => {
  let wrapper;
  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });
  test('Row selected when nodeResource id matches row id and clicking new row makes expected callback', async () => {
    JobTemplatesAPI.read.mockResolvedValueOnce({
      data: {
        count: 2,
        results: [
          {
            id: 1,
            name: 'Test Job Template',
            type: 'job_template',
            url: '/api/v2/job_templates/1',
            inventory: 1,
            project: 2,
          },
          {
            id: 2,
            name: 'Test Job Template 2',
            type: 'job_template',
            url: '/api/v2/job_templates/2',
            inventory: 1,
            project: 2,
          },
        ],
      },
    });
    JobTemplatesAPI.readOptions.mockResolvedValue({
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
        <JobTemplatesList
          nodeResource={nodeResource}
          onUpdateNodeResource={onUpdateNodeResource}
        />
      );
    });
    wrapper.update();
    expect(
      wrapper.find('CheckboxListItem[name="Test Job Template"]').props()
        .isSelected
    ).toBe(true);
    expect(
      wrapper.find('CheckboxListItem[name="Test Job Template"]').props()
        .isDisabled
    ).toBe(false);
    expect(
      wrapper.find('CheckboxListItem[name="Test Job Template 2"]').props()
        .isSelected
    ).toBe(false);
    expect(
      wrapper.find('CheckboxListItem[name="Test Job Template 2"]').props()
        .isDisabled
    ).toBe(false);
    wrapper
      .find('CheckboxListItem[name="Test Job Template 2"]')
      .simulate('click');
    expect(onUpdateNodeResource).toHaveBeenCalledWith({
      id: 2,
      name: 'Test Job Template 2',
      type: 'job_template',
      url: '/api/v2/job_templates/2',
      inventory: 1,
      project: 2,
    });
  });
  test('Row disabled when job template missing inventory or project', async () => {
    JobTemplatesAPI.read.mockResolvedValueOnce({
      data: {
        count: 2,
        results: [
          {
            id: 1,
            name: 'Test Job Template',
            type: 'job_template',
            url: '/api/v2/job_templates/1',
            inventory: 1,
            project: null,
            ask_inventory_on_launch: false,
          },
          {
            id: 2,
            name: 'Test Job Template 2',
            type: 'job_template',
            url: '/api/v2/job_templates/2',
            inventory: null,
            project: 2,
            ask_inventory_on_launch: false,
          },
        ],
      },
    });
    JobTemplatesAPI.readOptions.mockResolvedValue({
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
        <JobTemplatesList
          nodeResource={nodeResource}
          onUpdateNodeResource={onUpdateNodeResource}
        />
      );
    });
    wrapper.update();
    expect(
      wrapper.find('CheckboxListItem[name="Test Job Template"]').props()
        .isSelected
    ).toBe(true);
    expect(
      wrapper.find('CheckboxListItem[name="Test Job Template"]').props()
        .isDisabled
    ).toBe(true);
    expect(
      wrapper.find('CheckboxListItem[name="Test Job Template 2"]').props()
        .isSelected
    ).toBe(false);
    expect(
      wrapper.find('CheckboxListItem[name="Test Job Template 2"]').props()
        .isDisabled
    ).toBe(true);
    wrapper
      .find('CheckboxListItem[name="Test Job Template 2"]')
      .simulate('click');
    expect(onUpdateNodeResource).not.toHaveBeenCalled();
  });
  test('Error shown when read() request errors', async () => {
    JobTemplatesAPI.read.mockRejectedValue(new Error());
    JobTemplatesAPI.readOptions.mockResolvedValue({
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
        <JobTemplatesList
          nodeResource={nodeResource}
          onUpdateNodeResource={onUpdateNodeResource}
        />
      );
    });
    wrapper.update();
    expect(wrapper.find('ErrorDetail').length).toBe(1);
  });
});
