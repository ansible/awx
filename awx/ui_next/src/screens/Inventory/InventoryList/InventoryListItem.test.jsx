import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { InventoriesAPI } from '../../../api';
import InventoryListItem from './InventoryListItem';

jest.mock('../../../api/models/Inventories');

describe('<InventoryListItem />', () => {
  const inventory = {
    id: 1,
    name: 'Inventory',
    kind: '',
    has_active_failures: true,
    total_hosts: 10,
    hosts_with_active_failures: 4,
    has_inventory_sources: true,
    total_inventory_sources: 4,
    inventory_sources_with_failures: 5,
    summary_fields: {
      organization: {
        id: 1,
        name: 'Default',
      },
      user_capabilities: {
        edit: true,
      },
    },
  };

  test('initially renders successfully', () => {
    mountWithContexts(
      <table>
        <tbody>
          <InventoryListItem
            inventory={inventory}
            detailUrl="/inventories/inventory/1"
            isSelected
            onSelect={() => {}}
          />
        </tbody>
      </table>
    );
  });

  test('should render not configured tooltip', () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <InventoryListItem
            inventory={{ ...inventory, has_inventory_sources: false }}
            detailUrl="/inventories/inventory/1"
            isSelected
            onSelect={() => {}}
          />
        </tbody>
      </table>
    );

    expect(wrapper.find('StatusLabel').prop('tooltipContent')).toBe(
      'Not configured for inventory sync.'
    );
  });

  test('should render success tooltip', () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <InventoryListItem
            inventory={{ ...inventory, inventory_sources_with_failures: 0 }}
            detailUrl="/inventories/inventory/1"
            isSelected
            onSelect={() => {}}
          />
        </tbody>
      </table>
    );

    expect(wrapper.find('StatusLabel').prop('tooltipContent')).toBe(
      'No inventory sync failures.'
    );
  });

  test('should render prompt list item data', () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <InventoryListItem
            inventory={inventory}
            detailUrl="/inventories/inventory/1"
            isSelected
            onSelect={() => {}}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('StatusLabel').length).toBe(1);
    expect(wrapper.find('StatusLabel').prop('tooltipContent')).toBe(
      `${inventory.inventory_sources_with_failures} sources with sync failures.`
    );
    expect(
      wrapper
        .find('Td')
        .at(1)
        .text()
    ).toBe('Inventory');
    expect(
      wrapper
        .find('Td')
        .at(2)
        .text()
    ).toBe('Error');
    expect(
      wrapper
        .find('Td')
        .at(3)
        .text()
    ).toBe('Inventory');
    expect(
      wrapper
        .find('Td')
        .at(4)
        .text()
    ).toBe('Default');
  });

  test('edit button shown to users with edit capabilities', () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <InventoryListItem
            inventory={inventory}
            detailUrl="/inventories/inventory/1"
            isSelected
            onSelect={() => {}}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('PencilAltIcon').exists()).toBeTruthy();
  });

  test('edit button hidden from users without edit capabilities', () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <InventoryListItem
            inventory={{
              id: 1,
              name: 'Inventory',
              summary_fields: {
                organization: {
                  id: 1,
                  name: 'Default',
                },
                user_capabilities: {
                  edit: false,
                },
              },
            }}
            detailUrl="/inventories/inventory/1"
            isSelected
            onSelect={() => {}}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('PencilAltIcon').exists()).toBeFalsy();
  });

  test('should call api to copy inventory', async () => {
    InventoriesAPI.copy.mockResolvedValue();

    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <InventoryListItem
            inventory={{
              id: 1,
              name: 'Inventory',
              summary_fields: {
                organization: {
                  id: 1,
                  name: 'Default',
                },
                user_capabilities: {
                  edit: false,
                  copy: true,
                },
              },
            }}
            detailUrl="/inventories/inventory/1"
            isSelected
            onSelect={() => {}}
          />
        </tbody>
      </table>
    );

    await act(async () =>
      wrapper.find('Button[aria-label="Copy"]').prop('onClick')()
    );
    expect(InventoriesAPI.copy).toHaveBeenCalled();
    jest.clearAllMocks();
  });

  test('should render proper alert modal on copy error', async () => {
    InventoriesAPI.copy.mockRejectedValue(new Error());

    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <InventoryListItem
            inventory={{
              id: 1,
              name: 'Inventory',
              summary_fields: {
                organization: {
                  id: 1,
                  name: 'Default',
                },
                user_capabilities: {
                  edit: false,
                  copy: true,
                },
              },
            }}
            detailUrl="/inventories/inventory/1"
            isSelected
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
    jest.clearAllMocks();
  });

  test('should not render copy button', async () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <InventoryListItem
            inventory={{
              id: 1,
              name: 'Inventory',
              summary_fields: {
                organization: {
                  id: 1,
                  name: 'Default',
                },
                user_capabilities: {
                  edit: false,
                  copy: false,
                },
              },
            }}
            detailUrl="/inventories/inventory/1"
            isSelected
            onSelect={() => {}}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('CopyButton').length).toBe(0);
  });
});
