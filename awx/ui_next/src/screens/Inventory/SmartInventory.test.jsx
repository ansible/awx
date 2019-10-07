import React from 'react';
import { createMemoryHistory } from 'history';
import { InventoriesAPI } from '@api';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import mockSmartInventory from './shared/data.smart_inventory.json';
import SmartInventory from './SmartInventory';

jest.mock('@api');

InventoriesAPI.readDetail.mockResolvedValue({
  data: mockSmartInventory,
});

describe.only('<SmartInventory />', () => {
  test('initially renders succesfully', async done => {
    const wrapper = mountWithContexts(
      <SmartInventory setBreadcrumb={() => {}} match={{ params: { id: 1 } }} />
    );
    await waitForElement(
      wrapper,
      'SmartInventory',
      el => el.state('hasContentLoading') === true
    );
    await waitForElement(
      wrapper,
      'SmartInventory',
      el => el.state('hasContentLoading') === false
    );
    await waitForElement(wrapper, '.pf-c-tabs__item', el => el.length === 4);
    done();
  });
  test('should show content error when user attempts to navigate to erroneous route', async done => {
    const history = createMemoryHistory({
      initialEntries: ['/inventories/smart_inventory/1/foobar'],
    });
    const wrapper = mountWithContexts(
      <SmartInventory setBreadcrumb={() => {}} />,
      {
        context: {
          router: {
            history,
            route: {
              location: history.location,
              match: {
                params: { id: 1 },
                url: '/inventories/smart_inventory/1/foobar',
                path: '/inventories/smart_inventory/1/foobar',
              },
            },
          },
        },
      }
    );
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
    done();
  });
});
