import React from 'react';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import InventoryGroupHostListItem from './InventoryGroupHostListItem';
import mockHosts from '../shared/data.hosts.json';
import { Route } from 'react-router-dom';

jest.mock('../../../api');

describe('<InventoryGroupHostListItem />', () => {
  let wrapper;
  const mockHost = mockHosts.results[0];
  const history = createMemoryHistory({
    initialEntries: ['/inventories/inventory/1/groups/2/hosts'],
  });
  beforeEach(() => {
    wrapper = mountWithContexts(
      <Route path="/inventories/:inventoryType/:id/groups/:groupId/hosts">
        <table>
          <tbody>
            <InventoryGroupHostListItem
              detailUrl="/host/1"
              editUrl="/host/1"
              host={mockHost}
              isSelected={false}
              onSelect={() => {}}
              rowIndex={0}
            />
          </tbody>
        </table>
      </Route>,
      { context: { router: { history } } }
    );
  });

  test('should display expected details', () => {
    expect(wrapper.find('InventoryGroupHostListItem').length).toBe(1);
    expect(
      wrapper.find('Td[dataLabel="host-name-2"]').find('Link').prop('to')
    ).toBe('/host/1');
    expect(wrapper.find('Td[dataLabel="host-description-2"]').text()).toBe(
      'Bar'
    );
  });

  test('should display expected row item content', () => {
    expect(wrapper.find('b').text()).toContain(
      '.host-000001.group-00000.dummy'
    );
    expect(wrapper.find('Sparkline').length).toBe(1);
    expect(wrapper.find('HostToggle').length).toBe(1);
  });

  test('edit button shown to users with edit capabilities', () => {
    expect(wrapper.find('PencilAltIcon').exists()).toBeTruthy();
  });

  test('edit button hidden from users without edit capabilities', () => {
    const copyMockHost = { ...mockHost };
    copyMockHost.summary_fields.user_capabilities.edit = false;
    wrapper = mountWithContexts(
      <Route path="/inventories/:inventoryType/:id/groups/:groupId/hosts">
        <table>
          <tbody>
            <InventoryGroupHostListItem
              detailUrl="/host/1"
              editUrl="/host/1"
              host={mockHost}
              isSelected={false}
              onSelect={() => {}}
              rowIndex={0}
            />
          </tbody>
        </table>
      </Route>,
      { context: { router: { history } } }
    );
    expect(wrapper.find('PencilAltIcon').exists()).toBeFalsy();
  });
});

describe('<InventoryGroupHostListItem> inside constructed inventories', () => {
  jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
      id: 1,
      groupId: 2,
      inventoryType: 'constructed_inventory',
    }),
  }));
  let wrapper;
  const mockHost = mockHosts.results[0];
  const history = createMemoryHistory({
    initialEntries: ['/inventories/constructed_inventory/1/groups/2/hosts'],
  });
  beforeEach(() => {
    wrapper = mountWithContexts(
      <Route path="/inventories/:inventoryType/:id/groups/:groupId/hosts">
        <table>
          <tbody>
            <InventoryGroupHostListItem
              detailUrl="/host/1"
              editUrl="/host/1"
              host={mockHost}
              isSelected={false}
              onSelect={() => {}}
              rowIndex={0}
            />
          </tbody>
        </table>
      </Route>,
      { context: { router: { history } } }
    );
  });
  test('Edit button hidden for constructed inventory', () => {
    expect(wrapper.find('PencilAltIcon').exists()).toBeFalsy();
  });
});
