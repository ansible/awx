import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { ExecutionEnvironmentsAPI } from '../../../api';

import ExecutionEnvironmentEdit from './ExecutionEnvironmentEdit';

jest.mock('../../../api');

const mockMe = {
  is_superuser: true,
  is_system_auditor: false,
};

const executionEnvironmentData = {
  id: 42,
  credential: { id: 4 },
  description: 'A simple EE',
  image: 'https://registry.com/image/container',
  container_options: 'one',
  name: 'Test EE',
};

const updateExecutionEnvironmentData = {
  image: 'https://registry.com/image/container2',
  description: 'Updated new description',
};

const mockOptions = {
  data: {
    actions: {
      POST: {
        container_options: {
          choices: [
            ['one', 'One'],
            ['two', 'Two'],
            ['three', 'Three'],
          ],
        },
      },
    },
  },
};

ExecutionEnvironmentsAPI.readOptions.mockResolvedValue(mockOptions);

describe('<ExecutionEnvironmentEdit/>', () => {
  let wrapper;
  let history;

  beforeAll(async () => {
    history = createMemoryHistory();
    await act(async () => {
      wrapper = mountWithContexts(
        <ExecutionEnvironmentEdit
          executionEnvironment={executionEnvironmentData}
          me={mockMe}
        />,
        {
          context: { router: { history } },
        }
      );
    });
  });

  afterAll(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('handleSubmit should call the api and redirect to details page', async () => {
    await act(async () => {
      wrapper.find('ExecutionEnvironmentForm').invoke('onSubmit')(
        updateExecutionEnvironmentData
      );
      wrapper.update();
      expect(ExecutionEnvironmentsAPI.update).toHaveBeenCalledWith(42, {
        ...updateExecutionEnvironmentData,
        credential: null,
        organization: null,
      });
    });

    expect(history.location.pathname).toEqual(
      '/execution_environments/42/details'
    );
  });

  test('should navigate to execution environments details when cancel is clicked', async () => {
    await act(async () => {
      wrapper.find('button[aria-label="Cancel"]').prop('onClick')();
    });
    expect(history.location.pathname).toEqual(
      '/execution_environments/42/details'
    );
  });

  test('should navigate to execution environments detail after successful submission', async () => {
    await act(async () => {
      wrapper.find('ExecutionEnvironmentForm').invoke('onSubmit')({
        updateExecutionEnvironmentData,
      });
    });
    wrapper.update();
    expect(wrapper.find('FormSubmitError').length).toBe(0);
    expect(history.location.pathname).toEqual(
      '/execution_environments/42/details'
    );
  });

  test('failed form submission should show an error message', async () => {
    const error = {
      response: {
        data: { detail: 'An error occurred' },
      },
    };
    ExecutionEnvironmentsAPI.update.mockImplementationOnce(() =>
      Promise.reject(error)
    );
    await act(async () => {
      wrapper.find('ExecutionEnvironmentForm').invoke('onSubmit')(
        updateExecutionEnvironmentData
      );
    });
    wrapper.update();
    expect(wrapper.find('FormSubmitError').length).toBe(1);
  });
});
