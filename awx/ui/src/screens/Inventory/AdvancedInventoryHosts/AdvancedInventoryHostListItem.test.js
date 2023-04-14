import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import AdvancedInventoryHostListItem from './AdvancedInventoryHostListItem';

const mockHost = {
  id: 2,
  name: 'Host Two',
  url: '/api/v2/hosts/2',
  inventory: 1,
  summary_fields: {
    inventory: {
      id: 1,
      name: 'Inv 1',
    },
    user_capabilities: {
      edit: true,
    },
    recent_jobs: [],
  },
};

describe('<AdvancedInventoryHostListItem />', () => {
  let wrapper;

  beforeEach(() => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <AdvancedInventoryHostListItem
            detailUrl="/inventories/smart_inventory/1/hosts/2"
            host={mockHost}
            isSelected={false}
            onSelect={() => {}}
          />
        </tbody>
      </table>
    );
  });

  test('should render expected row cells', () => {
    const cells = wrapper.find('Td');
    expect(cells).toHaveLength(4);
    expect(cells.at(1).text()).toEqual('Host Two');
    expect(cells.at(2).find('Sparkline').length).toEqual(1);
    expect(cells.at(3).text()).toEqual('Inv 1');
  });
});
