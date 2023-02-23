import React from 'react';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import InventoryRelatedGroupListItem from './InventoryRelatedGroupListItem';
import mockRelatedGroups from '../shared/data.relatedGroups.json';
import { Route } from 'react-router-dom';

jest.mock('../../../api');

const mockGroup = mockRelatedGroups.results[0];
describe('<InventoryRelatedGroupListItem />', () => {
  let wrapper;
  const history = createMemoryHistory({
    initialEntries: ['/inventories/inventory/1/groups/2/nested_groups'],
  });
  jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
      id: 1,
      groupId: 2,
      inventoryType: 'inventory',
    }),
  }));
  beforeEach(() => {
    wrapper = mountWithContexts(
      <Route path="/inventories/:inventoryType/:id/groups/:groupId/nested_groups">
        <table>
          <tbody>
            <InventoryRelatedGroupListItem
              detailUrl="/group/1"
              editUrl="/group/1"
              group={mockGroup}
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

  test('should display expected row item content', () => {
    expect(wrapper.find('b').text()).toContain('Group 2 Inventory 0');
  });

  test('edit button shown to users with edit capabilities', () => {
    expect(wrapper.find('PencilAltIcon').exists()).toBeTruthy();
  });

  test('edit button hidden from users without edit capabilities', () => {
    wrapper = mountWithContexts(
      <Route path="/inventories/:inventoryType/:id/groups/:groupId/nested_groups">
        <table>
          <tbody>
            <InventoryRelatedGroupListItem
              detailUrl="/group/1"
              editUrl="/group/1"
              group={mockRelatedGroups.results[2]}
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

describe('<InventoryRelatedGroupList> for constructed inventories', () => {
  jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
      id: 1,
      groupId: 2,
      inventoryType: 'constructed_inventory',
    }),
  }));

  let wrapper;

  test('edit button hidden from users without edit capabilities', () => {
    const history = createMemoryHistory({
      initialEntries: [
        '/inventories/constructed_inventory/1/groups/2/nested_groups',
      ],
    });
    wrapper = mountWithContexts(
      <Route path="/inventories/:inventoryType/:id/groups/:groupId/nested_groups">
        <table>
          <tbody>
            <InventoryRelatedGroupListItem
              detailUrl="/group/1"
              editUrl="/group/1"
              group={mockGroup}
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
