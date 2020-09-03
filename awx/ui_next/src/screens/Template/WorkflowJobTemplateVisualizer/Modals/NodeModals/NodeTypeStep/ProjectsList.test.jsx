import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../../../../testUtils/enzymeHelpers';
import { ProjectsAPI } from '../../../../../../api';
import ProjectsList from './ProjectsList';

jest.mock('../../../../../../api/models/Projects');

const nodeResource = {
  id: 1,
  name: 'Test Project',
  unified_job_type: 'project_update',
};
const onUpdateNodeResource = jest.fn();

describe('ProjectsList', () => {
  let wrapper;
  afterEach(() => {
    wrapper.unmount();
  });
  test('Row selected when nodeResource id matches row id and clicking new row makes expected callback', async () => {
    ProjectsAPI.read.mockResolvedValueOnce({
      data: {
        count: 2,
        results: [
          {
            id: 1,
            name: 'Test Project',
            type: 'project',
            url: '/api/v2/projects/1',
          },
          {
            id: 2,
            name: 'Test Project 2',
            type: 'project',
            url: '/api/v2/projects/2',
          },
        ],
      },
    });
    ProjectsAPI.readOptions.mockResolvedValue({
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
        <ProjectsList
          nodeResource={nodeResource}
          onUpdateNodeResource={onUpdateNodeResource}
        />
      );
    });
    wrapper.update();
    expect(
      wrapper.find('CheckboxListItem[name="Test Project"]').props().isSelected
    ).toBe(true);
    expect(
      wrapper.find('CheckboxListItem[name="Test Project 2"]').props().isSelected
    ).toBe(false);
    wrapper.find('CheckboxListItem[name="Test Project 2"]').simulate('click');
    expect(onUpdateNodeResource).toHaveBeenCalledWith({
      id: 2,
      name: 'Test Project 2',
      type: 'project',
      url: '/api/v2/projects/2',
    });
  });
  test('Error shown when read() request errors', async () => {
    ProjectsAPI.read.mockRejectedValue(new Error());
    await act(async () => {
      wrapper = mountWithContexts(
        <ProjectsList
          nodeResource={nodeResource}
          onUpdateNodeResource={onUpdateNodeResource}
        />
      );
    });
    wrapper.update();
    expect(wrapper.find('ErrorDetail').length).toBe(1);
  });
});
