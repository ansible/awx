import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { ExecutionEnvironmentsAPI } from '../../../api';
import ExecutionEnvironmentAdd from './ExecutionEnvironmentAdd';

jest.mock('../../../api');

const mockMe = {
  is_superuser: true,
  is_system_auditor: false,
};

const executionEnvironmentData = {
  credential: 4,
  description: 'A simple EE',
  image: 'https://registry.com/image/container',
};

ExecutionEnvironmentsAPI.create.mockResolvedValue({
  data: {
    id: 42,
  },
});

describe('<ExecutionEnvironmentAdd/>', () => {
  let wrapper;
  let history;

  beforeEach(async () => {
    history = createMemoryHistory({
      initialEntries: ['/execution_environments'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<ExecutionEnvironmentAdd me={mockMe} />, {
        context: { router: { history } },
      });
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('handleSubmit should call the api and redirect to details page', async () => {
    await act(async () => {
      wrapper.find('ExecutionEnvironmentForm').prop('onSubmit')({
        executionEnvironmentData,
      });
    });
    wrapper.update();
    expect(ExecutionEnvironmentsAPI.create).toHaveBeenCalledWith({
      executionEnvironmentData,
    });
    expect(history.location.pathname).toBe(
      '/execution_environments/42/details'
    );
  });

  test('handleCancel should return the user back to the execution environments list', async () => {
    wrapper.find('Button[aria-label="Cancel"]').simulate('click');
    expect(history.location.pathname).toEqual('/execution_environments');
  });

  test('failed form submission should show an error message', async () => {
    const error = {
      response: {
        data: { detail: 'An error occurred' },
      },
    };
    ExecutionEnvironmentsAPI.create.mockImplementationOnce(() =>
      Promise.reject(error)
    );
    await act(async () => {
      wrapper.find('ExecutionEnvironmentForm').invoke('onSubmit')(
        executionEnvironmentData
      );
    });
    wrapper.update();
    expect(wrapper.find('FormSubmitError').length).toBe(1);
  });
});
