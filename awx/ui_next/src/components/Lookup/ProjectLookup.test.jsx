import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import { sleep } from '../../../testUtils/testUtils';
import { ProjectsAPI } from '../../api';
import ProjectLookup from './ProjectLookup';

jest.mock('../../api');

describe('<ProjectLookup />', () => {
  test('should auto-select project when only one available', async () => {
    ProjectsAPI.read.mockReturnValue({
      data: {
        results: [{ id: 1 }],
        count: 1,
      },
    });
    const autocomplete = jest.fn();
    await act(async () => {
      mountWithContexts(
        <ProjectLookup autocomplete={autocomplete} onChange={() => {}} />
      );
    });
    await sleep(0);
    expect(autocomplete).toHaveBeenCalledWith({ id: 1 });
  });

  test('should not auto-select project when multiple available', async () => {
    ProjectsAPI.read.mockReturnValue({
      data: {
        results: [{ id: 1 }, { id: 2 }],
        count: 2,
      },
    });
    const autocomplete = jest.fn();
    await act(async () => {
      mountWithContexts(
        <ProjectLookup autocomplete={autocomplete} onChange={() => {}} />
      );
    });
    await sleep(0);
    expect(autocomplete).not.toHaveBeenCalled();
  });
});
