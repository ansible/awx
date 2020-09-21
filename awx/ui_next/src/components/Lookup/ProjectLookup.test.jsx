import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import { ProjectsAPI } from '../../api';
import ProjectLookup from './ProjectLookup';

jest.mock('../../api');

describe('<ProjectLookup />', () => {
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
});
