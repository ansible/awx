import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { ExecutionEnvironmentsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import AdHocExecutionEnvironmentStep from './AdHocExecutionEnvironmentStep';

jest.mock('../../api/models/ExecutionEnvironments');

describe('<AdHocExecutionEnvironmentStep />', () => {
  let wrapper;
  beforeEach(async () => {
    ExecutionEnvironmentsAPI.read.mockResolvedValue({
      data: {
        results: [
          { id: 1, name: 'EE1 1', url: 'wwww.google.com' },
          { id: 2, name: 'EE2', url: 'wwww.google.com' },
        ],
        count: 2,
      },
    });
    ExecutionEnvironmentsAPI.readOptions.mockResolvedValue({
      data: { actions: { GET: {} } },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik>
          <AdHocExecutionEnvironmentStep organizationId={1} />
        </Formik>
      );
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should mount properly', async () => {
    await waitForElement(wrapper, 'OptionsList', (el) => el.length > 0);
  });

  test('should call api', async () => {
    await waitForElement(wrapper, 'OptionsList', (el) => el.length > 0);
    expect(ExecutionEnvironmentsAPI.read).toHaveBeenCalled();
    expect(wrapper.find('CheckboxListItem').length).toBe(2);
  });
});
