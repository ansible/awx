import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { ProjectsAPI } from 'api';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import ProjectLookup from './ProjectLookup';

jest.mock('../../api');

describe('<ProjectLookup />', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should auto-select project when only one available and autoPopulate prop is true', async () => {
    ProjectsAPI.read.mockReturnValue({
      data: {
        results: [{ id: 1, name: 'Test' }],
        count: 1,
      },
    });
    const onChange = jest.fn();
    await act(async () => {
      mountWithContexts(
        <Formik>
          <ProjectLookup autoPopulate onChange={onChange} />
        </Formik>
      );
    });
    expect(onChange).toHaveBeenCalledWith({ id: 1, name: 'Test' });
  });

  test('should not auto-select project when autoPopulate prop is false', async () => {
    ProjectsAPI.read.mockReturnValue({
      data: {
        results: [{ id: 1, name: 'Test' }],
        count: 1,
      },
    });
    const onChange = jest.fn();
    await act(async () => {
      mountWithContexts(
        <Formik>
          <ProjectLookup onChange={onChange} />
        </Formik>
      );
    });
    expect(onChange).not.toHaveBeenCalled();
  });

  test('should not auto-select project when multiple available', async () => {
    ProjectsAPI.read.mockReturnValue({
      data: {
        results: [
          { id: 1, name: 'Test' },
          { id: 2, name: 'Test 2' },
        ],
        count: 2,
      },
    });
    const onChange = jest.fn();
    await act(async () => {
      mountWithContexts(
        <Formik>
          <ProjectLookup autoPopulate onChange={onChange} />
        </Formik>
      );
    });
    expect(onChange).not.toHaveBeenCalled();
  });

  test('project lookup should be enabled', async () => {
    let wrapper;
    ProjectsAPI.read.mockReturnValue({
      data: {
        results: [{ id: 1, name: 'Test' }],
        count: 1,
      },
    });
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
        <Formik>
          <ProjectLookup isOverrideDisabled onChange={() => {}} />
        </Formik>
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
      wrapper = mountWithContexts(
        <Formik>
          <ProjectLookup onChange={() => {}} />
        </Formik>
      );
    });
    wrapper.update();
    expect(ProjectsAPI.read).toHaveBeenCalledTimes(1);
    expect(wrapper.find('ProjectLookup')).toHaveLength(1);
    expect(wrapper.find('Lookup').prop('isDisabled')).toBe(true);
  });

  test('should not show helper text', async () => {
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
        <Formik>
          <ProjectLookup
            isValid
            helperTextInvalid="select value"
            onChange={() => {}}
          />
        </Formik>
      );
    });
    wrapper.update();

    expect(wrapper.find('div#project-helper').length).toBe(0);
  });

  test('should not show helper text', async () => {
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
        <Formik>
          <ProjectLookup
            isValid={false}
            helperTextInvalid="select value"
            onChange={() => {}}
          />
        </Formik>
      );
    });
    wrapper.update();

    expect(wrapper.find('div#project-helper').text('helperTextInvalid')).toBe(
      'select value'
    );
  });
});
