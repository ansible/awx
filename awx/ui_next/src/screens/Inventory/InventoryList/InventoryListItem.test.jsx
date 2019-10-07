import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import InventoryListItem from './InventoryListItem';

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
});
