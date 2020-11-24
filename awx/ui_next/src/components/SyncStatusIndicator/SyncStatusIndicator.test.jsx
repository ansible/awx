import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import SyncStatusIndicator from './SyncStatusIndicator';

const mockInventory = {
  id: 1,
  type: 'inventory',
  url: '/api/v2/inventories/1/',
  name: 'Demo Inventory',
  description: '',
  organization: 1,
  kind: '',
  has_active_failures: true,
  total_hosts: 10,
  hosts_with_active_failures: 4,
  has_inventory_sources: true,
  total_inventory_sources: 4,
  inventory_sources_with_failures: 5,
};

describe('<SyncStatusIndicator />', () => {
  test('should render syncing tooltip', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <SyncStatusIndicator status="syncing" inventory={mockInventory} />
      );
    });

    expect(wrapper.find('Tooltip').prop('content')).toBe('Syncing');
  });

  test('should render error tooltip', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <SyncStatusIndicator status="error" inventory={mockInventory} />
      );
    });

    expect(wrapper.find('Tooltip').prop('content')).toBe(
      `${mockInventory.inventory_sources_with_failures} sources with sync failures.`
    );
  });

  test('should render success tooltip', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <SyncStatusIndicator
          status="success"
          inventory={{
            ...mockInventory,
            inventory_sources_with_failures: 0,
          }}
        />
      );
    });

    expect(wrapper.find('Tooltip').prop('content')).toBe(
      'No inventory sync failures.'
    );
  });

  test('should render not configured tooltip', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <SyncStatusIndicator
          status="disabled"
          inventory={{
            ...mockInventory,
            has_inventory_sources: false,
          }}
        />
      );
    });

    expect(wrapper.find('Tooltip').prop('content')).toBe(
      'Not configured for inventory sync.'
    );
  });
});
