import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import AdvancedInventoryHosts from './AdvancedInventoryHosts';

jest.mock('../../../api');
jest.mock('./AdvancedInventoryHostList', () => {
  const AdvancedInventoryHostList = () => <div />;
  return {
    __esModule: true,
    default: AdvancedInventoryHostList,
  };
});

describe('<AdvancedInventoryHosts />', () => {
  test('should render smart inventory host list', () => {
    const history = createMemoryHistory({
      initialEntries: ['/inventories/smart_inventory/1/hosts'],
    });
    const match = {
      path: '/inventories/:inventoryType/:id/hosts',
      url: '/inventories/smart_inventory/1/hosts',
      isExact: true,
    };
    const wrapper = mountWithContexts(
      <AdvancedInventoryHosts inventory={{ id: 1 }} />,
      {
        context: { router: { history, route: { match } } },
      }
    );
    expect(wrapper.find('AdvancedInventoryHostList').length).toBe(1);
    expect(wrapper.find('AdvancedInventoryHostList').prop('inventory')).toEqual(
      {
        id: 1,
      }
    );
    jest.clearAllMocks();
  });

  test('should render smart inventory host details', async () => {
    let wrapper;
    const history = createMemoryHistory({
      initialEntries: ['/inventories/smart_inventory/1/hosts/2'],
    });
    const match = {
      path: '/inventories/:inventoryType/:id/hosts/:hostId',
      url: '/inventories/smart_inventory/1/hosts/2',
      isExact: true,
    };
    await act(async () => {
      wrapper = mountWithContexts(
        <AdvancedInventoryHosts
          inventory={{ id: 1 }}
          setBreadcrumb={() => {}}
        />,
        {
          context: { router: { history, route: { match } } },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('AdvancedInventoryHost').length).toBe(1);
    jest.clearAllMocks();
  });
});
