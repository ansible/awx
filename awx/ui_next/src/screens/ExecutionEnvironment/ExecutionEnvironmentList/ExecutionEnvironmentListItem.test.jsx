import React from 'react';
import { act } from 'react-dom/test-utils';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import ExecutionEnvironmentListItem from './ExecutionEnvironmentListItem';

describe('<ExecutionEnvironmentListItem/>', () => {
  let wrapper;
  const executionEnvironment = {
    id: 1,
    image: 'https://registry.com/r/image/manifest',
    organization: 1,
    credential: null,
    url: '/api/v2/execution_environments/1/',
    summary_fields: {
      user_capabilities: { edit: true, delete: true },
      organization: {
        id: 1,
        name: 'Default',
        description: '',
      },
    },
  };

  test('should mount successfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ExecutionEnvironmentListItem
          executionEnvironment={executionEnvironment}
          detailUrl="execution_environments/1/details"
          isSelected={false}
          onSelect={() => {}}
        />
      );
    });
    expect(wrapper.find('ExecutionEnvironmentListItem').length).toBe(1);
  });

  test('should render the proper data when organization is available', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ExecutionEnvironmentListItem
          executionEnvironment={executionEnvironment}
          detailUrl="execution_environments/1/details"
          isSelected={false}
          onSelect={() => {}}
        />
      );
    });
    expect(
      wrapper
        .find('DataListCell[aria-label="execution environment image"]')
        .text()
    ).toBe(executionEnvironment.image);
    expect(
      wrapper
        .find('DataListCell[aria-label="execution environment organization"]')
        .text()
    ).toBe('Organization Default');
    expect(wrapper.find('PencilAltIcon').length).toBe(1);
    expect(
      wrapper.find('input#select-execution-environment-1').prop('checked')
    ).toBe(false);
  });

  test('should render the proper data when organization is not available', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ExecutionEnvironmentListItem
          executionEnvironment={{
            ...executionEnvironment,
            organization: null,
            summary_fields: null,
          }}
          detailUrl="execution_environments/1/details"
          isSelected={false}
          onSelect={() => {}}
        />
      );
    });
    expect(
      wrapper
        .find('DataListCell[aria-label="execution environment image"]')
        .text()
    ).toBe(executionEnvironment.image);
    expect(
      wrapper
        .find('DataListCell[aria-label="execution environment organization"]')
        .text()
    ).toBe('Globally available');
    expect(wrapper.find('PencilAltIcon').length).toBe(1);
    expect(
      wrapper.find('input#select-execution-environment-1').prop('checked')
    ).toBe(false);
  });
});
