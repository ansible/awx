import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
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

  test('should render smart inventory host details', async () => {
    let wrapper;
    const history = createMemoryHistory({
      initialEntries: ['/inventories/smart_inventory/1/hosts/2'],
    });
    const match = {
      path: '/inventories/smart_inventory/:id/hosts/:hostId',
      url: '/inventories/smart_inventory/1/hosts/2',
      isExact: true,
    };
    await act(async () => {
      wrapper = mountWithContexts(
        <SmartInventoryHosts inventory={{ id: 1 }} setBreadcrumb={() => {}} />,
        {
          context: { router: { history, route: { match } } },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('SmartInventoryHost').length).toBe(1);
    jest.clearAllMocks();
    wrapper.unmount();
  });
});
