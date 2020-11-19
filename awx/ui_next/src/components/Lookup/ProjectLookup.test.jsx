import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import { ProjectsAPI } from '../../api';
import ProjectLookup from './ProjectLookup';

jest.mock('../../api');

describe('<ProjectLookup />', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should auto-select project when only one available and autoPopulate prop is true', async () => {
    ProjectsAPI.read.mockReturnValue({
      data: {
        results: [{ id: 1 }],
        count: 1,
      },
    });
    const onChange = jest.fn();
    await act(async () => {
      mountWithContexts(<ProjectLookup autoPopulate onChange={onChange} />);
    });
    expect(onChange).toHaveBeenCalledWith({ id: 1 });
  });

  test('should not auto-select project when autoPopulate prop is false', async () => {
    ProjectsAPI.read.mockReturnValue({
      data: {
        results: [{ id: 1 }],
        count: 1,
      },
    });
    const onChange = jest.fn();
    await act(async () => {
      mountWithContexts(<ProjectLookup onChange={onChange} />);
    });
    expect(onChange).not.toHaveBeenCalled();
  });

  test('should not auto-select project when multiple available', async () => {
    ProjectsAPI.read.mockReturnValue({
      data: {
        results: [{ id: 1 }, { id: 2 }],
        count: 2,
      },
    });
    const onChange = jest.fn();
    await act(async () => {
      mountWithContexts(<ProjectLookup autoPopulate onChange={onChange} />);
    });
    expect(onChange).not.toHaveBeenCalled();
  });

  test('project lookup should be enabled', async () => {
    let wrapper;

    ProjectsAPI.readOptions.mockReturnValue({
      data: {
        actions: {
          GET: {},
        },
        related_search_fields: [],
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <ProjectLookup isOverrideDisabled onChange={() => {}} />
      );
    });
    wrapper.update();
    expect(ProjectsAPI.read).toHaveBeenCalledTimes(1);
    expect(wrapper.find('ProjectLookup')).toHaveLength(1);
    expect(wrapper.find('Lookup').prop('isDisabled')).toBe(false);
  });

  test('project lookup should be disabled', async () => {
    let wrapper;

    ProjectsAPI.readOptions.mockReturnValue({
      data: {
        actions: {
          GET: {},
        },
        related_search_fields: [],
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(<ProjectLookup onChange={() => {}} />);
    });
    wrapper.update();
    expect(ProjectsAPI.read).toHaveBeenCalledTimes(1);
    expect(wrapper.find('ProjectLookup')).toHaveLength(1);
    expect(wrapper.find('Lookup').prop('isDisabled')).toBe(true);
  });
});
