import React from 'react';
import { act } from 'react-dom/test-utils';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import ExecutionEnvironmentListItem from './ExecutionEnvironmentListItem';
import { ExecutionEnvironmentsAPI } from '../../../api';

jest.mock('../../../api');

describe('<ExecutionEnvironmentListItem/>', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  let wrapper;
  const executionEnvironment = {
    name: 'Foo',
    id: 1,
    image: 'https://registry.com/r/image/manifest',
    organization: null,
    credential: null,
    summary_fields: {
      user_capabilities: { edit: true, copy: true, delete: true },
    },
  };

  test('should mount successfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <table>
          <tbody>
            <ExecutionEnvironmentListItem
              executionEnvironment={executionEnvironment}
              detailUrl="execution_environments/1/details"
              isSelected={false}
              onSelect={() => {}}
            />
          </tbody>
        </table>
      );
    });
    expect(wrapper.find('ExecutionEnvironmentListItem').length).toBe(1);
  });

  test('should render the proper data', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <table>
          <tbody>
            <ExecutionEnvironmentListItem
              executionEnvironment={executionEnvironment}
              detailUrl="execution_environments/1/details"
              isSelected={false}
              onSelect={() => {}}
            />
          </tbody>
        </table>
      );
    });
    expect(
      wrapper
        .find('Td')
        .at(1)
        .text()
    ).toBe(executionEnvironment.name);
    expect(
      wrapper
        .find('Td')
        .at(2)
        .text()
    ).toBe(executionEnvironment.image);

    expect(
      wrapper
        .find('Td')
        .at(3)
        .text()
    ).toBe('Globally Available');

    expect(wrapper.find('PencilAltIcon').exists()).toBeTruthy();
  });

  test('should call api to copy execution environment', async () => {
    ExecutionEnvironmentsAPI.copy.mockResolvedValue();

    wrapper = mountWithContexts(
      <table>
        <tbody>
          <ExecutionEnvironmentListItem
            executionEnvironment={executionEnvironment}
            detailUrl="execution_environments/1/details"
            isSelected={false}
            onSelect={() => {}}
          />
        </tbody>
      </table>
    );

    await act(async () =>
      wrapper.find('Button[aria-label="Copy"]').prop('onClick')()
    );
    expect(ExecutionEnvironmentsAPI.copy).toHaveBeenCalled();
  });

  test('should render proper alert modal on copy error', async () => {
    ExecutionEnvironmentsAPI.copy.mockRejectedValue(new Error());

    wrapper = mountWithContexts(
      <table>
        <tbody>
          <ExecutionEnvironmentListItem
            executionEnvironment={executionEnvironment}
            detailUrl="execution_environments/1/details"
            isSelected={false}
            onSelect={() => {}}
          />
        </tbody>
      </table>
    );

    await act(async () =>
      wrapper.find('Button[aria-label="Copy"]').prop('onClick')()
    );
    wrapper.update();
    expect(wrapper.find('Modal').prop('isOpen')).toBe(true);
  });

  test('should not render copy button', async () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <ExecutionEnvironmentListItem
            executionEnvironment={{
              ...executionEnvironment,
              summary_fields: { user_capabilities: { copy: false } },
            }}
            detailUrl="execution_environments/1/details"
            isSelected={false}
            onSelect={() => {}}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('CopyButton').length).toBe(0);
  });
});
