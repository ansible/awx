import React from 'react';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import SmartInventoryHosts from './SmartInventoryHosts';

jest.mock('../../../api');

describe('<SmartInventoryHosts />', () => {
  test('should render smart inventory host list', () => {
    const history = createMemoryHistory({
      initialEntries: ['/inventories/smart_inventory/1/hosts'],
    });
    const match = {
      path: '/inventories/smart_inventory/:id/hosts',
      url: '/inventories/smart_inventory/1/hosts',
      isExact: true,
    };
    const wrapper = mountWithContexts(
      <SmartInventoryHosts inventory={{ id: 1 }} />,
      {
        context: { router: { history, route: { match } } },
      }
    );
    expect(wrapper.find('SmartInventoryHostList').length).toBe(1);
    jest.clearAllMocks();
    wrapper.unmount();
  });
});
