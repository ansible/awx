import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { ExecutionEnvironmentsAPI } from 'api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import ExecutionEnvironmentStep from './ExecutionEnvironmentStep';

jest.mock('../../../api/models/ExecutionEnvironments');

const execution_environments = [
  { id: 1, name: 'ee one', url: '/execution_environments/1' },
  { id: 2, name: 'ee two', url: '/execution_environments/2' },
  { id: 3, name: 'ee three', url: '/execution_environments/3' },
];

describe('ExecutionEnvironmentStep', () => {
  beforeEach(() => {
    ExecutionEnvironmentsAPI.read.mockResolvedValue({
      data: {
        results: execution_environments,
        count: 3,
      },
    });

    ExecutionEnvironmentsAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
      },
    });
  });

  test('should load execution environments', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik>
          <ExecutionEnvironmentStep />
        </Formik>
      );
    });
    wrapper.update();

    expect(ExecutionEnvironmentsAPI.read).toHaveBeenCalled();
    expect(wrapper.find('OptionsList').prop('options')).toEqual(
      execution_environments
    );
  });
});
