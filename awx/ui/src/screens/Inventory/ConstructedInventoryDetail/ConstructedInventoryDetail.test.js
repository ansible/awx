import React from 'react';
import { act } from 'react-dom/test-utils';
import { InventoriesAPI, CredentialTypesAPI } from 'api';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import ConstructedInventoryDetail from './ConstructedInventoryDetail';

jest.mock('../../../api');

const mockInventory = {
  id: 1,
  type: 'inventory',
  summary_fields: {
    organization: {
      id: 1,
      name: 'The Organization',
      description: '',
    },
    created_by: {
      username: 'the_creator',
      id: 2,
    },
    modified_by: {
      username: 'the_modifier',
      id: 3,
    },
    user_capabilities: {
      edit: true,
      delete: true,
      copy: true,
      adhoc: true,
    },
  },
  created: '2019-10-04T16:56:48.025455Z',
  modified: '2019-10-04T16:56:48.025468Z',
  name: 'Constructed Inv',
  description: '',
  organization: 1,
  kind: 'constructed',
  has_active_failures: false,
  total_hosts: 0,
  hosts_with_active_failures: 0,
  total_groups: 0,
  groups_with_active_failures: 0,
  has_inventory_sources: false,
  total_inventory_sources: 0,
  inventory_sources_with_failures: 0,
  pending_deletion: false,
  prevent_instance_group_fallback: false,
  update_cache_timeout: 0,
  limit: '',
  verbosity: 1,
};

describe('<ConstructedInventoryDetail />', () => {
  test('initially renders successfully', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <ConstructedInventoryDetail inventory={mockInventory} />
      );
    });
    expect(wrapper.length).toBe(1);
    expect(wrapper.find('ConstructedInventoryDetail').length).toBe(1);
  });
});
