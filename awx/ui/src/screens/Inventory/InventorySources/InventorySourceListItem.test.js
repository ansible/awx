import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import InventorySourceListItem from './InventorySourceListItem';

const source = {
  id: 1,
  name: 'Foo',
  source: 'Source Bar',
  summary_fields: {
    user_capabilities: { start: true, edit: true },
    last_job: {
      canceled_on: '2020-04-30T18:56:46.054087Z',
      description: '',
      failed: true,
      finished: '2020-04-30T18:56:46.054031Z',
      id: 664,
      license_error: false,
      name: ' Inventory 1 Org 0 - source 4',
      status: 'canceled',
    },
  },
};
describe('<InventorySourceListItem />', () => {
  let wrapper;
  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should mount properly', () => {
    const onSelect = jest.fn();
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <InventorySourceListItem
            source={source}
            isSelected={false}
            onSelect={onSelect}
            label="Source Bar"
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('InventorySourceListItem').length).toBe(1);
  });

  test('all buttons and text fields should render properly', () => {
    const onSelect = jest.fn();
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <InventorySourceListItem
            source={source}
            isSelected={false}
            onSelect={onSelect}
            label="Source Bar"
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('StatusLabel').length).toBe(1);
    expect(wrapper.find('Link').at(1).prop('to')).toBe('/jobs/inventory/664');
    expect(wrapper.find('.pf-c-table__check').length).toBe(1);
    expect(wrapper.find('Td').at(1).text()).toBe('Foo');
    expect(wrapper.find('Td').at(3).text()).toBe('Source Bar');
    expect(wrapper.find('InventorySourceSyncButton').length).toBe(1);
    expect(wrapper.find('PencilAltIcon').length).toBe(1);
  });

  test('item should be checked', () => {
    const onSelect = jest.fn();
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <InventorySourceListItem
            source={source}
            isSelected
            onSelect={onSelect}
            label="Source Bar"
          />
        </tbody>
      </table>
    );
    wrapper.update();
    expect(wrapper.find('.pf-c-table__check').length).toBe(1);
    expect(wrapper.find('Td').first().prop('select').isSelected).toEqual(true);
  });

  test('should not render status icon', () => {
    const onSelect = jest.fn();
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <InventorySourceListItem
            source={{
              ...source,
              summary_fields: {
                user_capabilities: { start: true, edit: true },
                last_job: null,
              },
            }}
            isSelected={false}
            onSelect={onSelect}
            label="Source Bar"
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('StatusIcon').length).toBe(0);
  });

  test('should not render sync buttons', async () => {
    const onSelect = jest.fn();
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <InventorySourceListItem
            source={{
              ...source,
              summary_fields: {
                user_capabilities: { start: false, edit: true },
              },
            }}
            isSelected={false}
            onSelect={onSelect}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('InventorySourceSyncButton').length).toBe(0);
    expect(wrapper.find('Button[aria-label="Edit Source"]').length).toBe(1);
  });

  test('should not render edit buttons', async () => {
    const onSelect = jest.fn();
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <InventorySourceListItem
            source={{
              ...source,
              summary_fields: {
                user_capabilities: { start: true, edit: false },
              },
            }}
            isSelected={false}
            onSelect={onSelect}
            label="Source Bar"
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('Button[aria-label="Edit Source"]').length).toBe(0);
    expect(wrapper.find('InventorySourceSyncButton').length).toBe(1);
  });

  test('should render warning about missing execution environment', () => {
    const onSelect = jest.fn();
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <InventorySourceListItem
            source={{
              ...source,
              custom_virtualenv: '/var/lib/awx/env',
              execution_environment: null,
            }}
            isSelected={false}
            onSelect={onSelect}
            label="Source Bar"
          />
        </tbody>
      </table>
    );
    expect(
      wrapper.find('.missing-execution-environment').prop('content')
    ).toEqual(
      'Custom virtual environment /var/lib/awx/env must be replaced by an execution environment.'
    );
  });

  test('should render cancel button while job is running', () => {
    const onSelect = jest.fn();
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <InventorySourceListItem
            source={{
              ...source,
              status: 'running',
              summary_fields: {
                ...source.summary_fields,
                current_job: {
                  id: 1000,
                  status: 'running',
                },
              },
              custom_virtualenv: '/var/lib/awx/env',
              execution_environment: null,
            }}
            isSelected={false}
            onSelect={onSelect}
            label="Source Bar"
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('JobCancelButton').length).toBe(1);
  });
});
