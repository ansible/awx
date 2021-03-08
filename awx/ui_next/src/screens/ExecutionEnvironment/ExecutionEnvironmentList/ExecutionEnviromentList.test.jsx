import React from 'react';
import { act } from 'react-dom/test-utils';

import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';

import { ExecutionEnvironmentsAPI } from '../../../api';
import ExecutionEnvironmentList from './ExecutionEnvironmentList';

jest.mock('../../../api/models/ExecutionEnvironments');

const executionEnvironments = {
  data: {
    results: [
      {
        name: 'Foo',
        id: 1,
        image: 'https://registry.com/r/image/manifest',
        organization: null,
        credential: null,
        url: '/api/v2/execution_environments/1/',
        summary_fields: { user_capabilities: { edit: true, delete: true } },
      },
      {
        name: 'Bar',
        id: 2,
        image: 'https://registry.com/r/image2/manifest',
        organization: null,
        credential: null,
        url: '/api/v2/execution_environments/2/',
        summary_fields: { user_capabilities: { edit: false, delete: true } },
      },
    ],
    count: 2,
  },
};

const options = { data: { actions: { POST: true } } };

describe('<ExecutionEnvironmentList/>', () => {
  beforeEach(() => {
    ExecutionEnvironmentsAPI.read.mockResolvedValue(executionEnvironments);
    ExecutionEnvironmentsAPI.readOptions.mockResolvedValue(options);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });
  let wrapper;

  test('should mount successfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<ExecutionEnvironmentList />);
    });
    await waitForElement(
      wrapper,
      'ExecutionEnvironmentList',
      el => el.length > 0
    );
  });

  test('should have data fetched and render 2 rows', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<ExecutionEnvironmentList />);
    });
    await waitForElement(
      wrapper,
      'ExecutionEnvironmentList',
      el => el.length > 0
    );

    expect(wrapper.find('ExecutionEnvironmentListItem').length).toBe(2);
    expect(ExecutionEnvironmentsAPI.read).toBeCalled();
    expect(ExecutionEnvironmentsAPI.readOptions).toBeCalled();
  });

  test('should delete items successfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<ExecutionEnvironmentList />);
    });
    await waitForElement(
      wrapper,
      'ExecutionEnvironmentList',
      el => el.length > 0
    );

    await act(async () => {
      wrapper
        .find('ExecutionEnvironmentListItem')
        .at(0)
        .invoke('onSelect')();
    });
    wrapper.update();
    await act(async () => {
      wrapper
        .find('ExecutionEnvironmentListItem')
        .at(1)
        .invoke('onSelect')();
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('ToolbarDeleteButton').invoke('onDelete')();
    });

    expect(ExecutionEnvironmentsAPI.destroy).toHaveBeenCalledTimes(2);
  });

  test('should render deletion error modal', async () => {
    ExecutionEnvironmentsAPI.destroy.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'DELETE',
            url: '/api/v2/execution_environments',
          },
          data: 'An error occurred',
        },
      })
    );
    await act(async () => {
      wrapper = mountWithContexts(<ExecutionEnvironmentList />);
    });
    waitForElement(wrapper, 'ExecutionEnvironmentList', el => el.length > 0);

    wrapper
      .find('ExecutionEnvironmentListItem')
      .at(0)
      .find('input')
      .simulate('change', 'a');
    wrapper.update();

    expect(
      wrapper
        .find('ExecutionEnvironmentListItem')
        .at(0)
        .find('input')
        .prop('checked')
    ).toBe(true);

    await act(async () =>
      wrapper.find('Button[aria-label="Delete"]').prop('onClick')()
    );
    wrapper.update();

    await act(async () =>
      wrapper.find('Button[aria-label="confirm delete"]').prop('onClick')()
    );
    wrapper.update();
    expect(wrapper.find('ErrorDetail').length).toBe(1);
  });

  test('should thrown content error', async () => {
    ExecutionEnvironmentsAPI.read.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'GET',
            url: '/api/v2/execution_environments',
          },
          data: 'An error occurred',
        },
      })
    );
    await act(async () => {
      wrapper = mountWithContexts(<ExecutionEnvironmentList />);
    });
    await waitForElement(
      wrapper,
      'ExecutionEnvironmentList',
      el => el.length > 0
    );
    expect(wrapper.find('ContentError').length).toBe(1);
  });

  test('should not render add button', async () => {
    ExecutionEnvironmentsAPI.read.mockResolvedValue(executionEnvironments);
    ExecutionEnvironmentsAPI.readOptions.mockResolvedValue({
      data: { actions: { POST: false } },
    });
    await act(async () => {
      wrapper = mountWithContexts(<ExecutionEnvironmentList />);
    });
    waitForElement(wrapper, 'ExecutionEnvironmentList', el => el.length > 0);
    expect(wrapper.find('ToolbarAddButton').length).toBe(0);
  });
});
