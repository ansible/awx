import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { InventoriesAPI } from '../../../api';
import InventoryListItem from './InventoryListItem';

jest.mock('../../../api/models/Inventories');

describe('<InventoryListItem />', () => {
  test('initially renders succesfully', () => {
    mountWithContexts(
      <I18nProvider>
        <MemoryRouter initialEntries={['/inventories']} initialIndex={0}>
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
                  edit: true,
                },
              },
            }}
            detailUrl="/inventories/inventory/1"
            isSelected
            onSelect={() => {}}
          />
        </MemoryRouter>
      </I18nProvider>
    );
  });
  test('edit button shown to users with edit capabilities', () => {
    const wrapper = mountWithContexts(
      <I18nProvider>
        <MemoryRouter initialEntries={['/inventories']} initialIndex={0}>
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
                  edit: true,
                },
              },
            }}
            detailUrl="/inventories/inventory/1"
            isSelected
            onSelect={() => {}}
          />
        </MemoryRouter>
      </I18nProvider>
    );
    expect(wrapper.find('PencilAltIcon').exists()).toBeTruthy();
  });
  test('edit button hidden from users without edit capabilities', () => {
    const wrapper = mountWithContexts(
      <I18nProvider>
        <MemoryRouter initialEntries={['/inventories']} initialIndex={0}>
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
        </MemoryRouter>
      </I18nProvider>
    );
    expect(wrapper.find('PencilAltIcon').exists()).toBeFalsy();
  });
  test('should call api to copy inventory', async () => {
    InventoriesAPI.copy.mockResolvedValue();

    const wrapper = mountWithContexts(
      <I18nProvider>
        <MemoryRouter initialEntries={['/inventories']} initialIndex={0}>
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
        </MemoryRouter>
      </I18nProvider>
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
      <I18nProvider>
        <MemoryRouter initialEntries={['/inventories']} initialIndex={0}>
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
        </MemoryRouter>
      </I18nProvider>
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
      <I18nProvider>
        <MemoryRouter initialEntries={['/inventories']} initialIndex={0}>
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
        </MemoryRouter>
      </I18nProvider>
    );
    expect(wrapper.find('CopyButton').length).toBe(0);
  });
});
