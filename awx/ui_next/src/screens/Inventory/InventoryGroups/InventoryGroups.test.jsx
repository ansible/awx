import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import InventoryGroups from './InventoryGroups';

jest.mock('../../../api');

describe('<InventoryGroups />', () => {
  test('initially renders successfully', async () => {
    let wrapper;
    const history = createMemoryHistory({
      initialEntries: ['/inventories/inventory/1/groups'],
    });
    const inventory = { id: 1, name: 'Foo' };

    await act(async () => {
      wrapper = mountWithContexts(
        <InventoryGroups setBreadcrumb={() => {}} inventory={inventory} />,

        {
          context: {
            router: { history, route: { location: history.location } },
          },
        }
      );
    });
    expect(wrapper.length).toBe(1);
    expect(wrapper.find('InventoryGroupsList').length).toBe(1);
  });
  test('test that InventoryGroupsAdd renders', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/inventories/inventory/1/groups/add'],
    });
    const inventory = { id: 1, name: 'Foo' };
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <InventoryGroups setBreadcrumb={() => {}} inventory={inventory} />,
        {
          context: {
            router: { history, route: { location: history.location } },
          },
        }
      );
    });
    expect(wrapper.find('InventoryGroupsAdd').length).toBe(1);
  });
});
