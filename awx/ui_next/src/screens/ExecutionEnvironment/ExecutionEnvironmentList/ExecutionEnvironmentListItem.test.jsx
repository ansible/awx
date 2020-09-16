import React from 'react';
import { act } from 'react-dom/test-utils';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import ExecutionEnvironmentListItem from './ExecutionEnvironmentListItem';

describe('<ExecutionEnvironmentListItem/>', () => {
  let wrapper;
  const executionEnvironment = {
    id: 1,
    image: 'https://registry.com/r/image/manifest',
    organization: null,
    credential: null,
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

  test('should render the proper data', async () => {
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
    expect(wrapper.find('PencilAltIcon').length).toBe(1);
    expect(
      wrapper.find('input#select-execution-environment-1').prop('checked')
    ).toBe(false);
  });
});
