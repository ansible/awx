import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import SmartInventoryHostListItem from './SmartInventoryHostListItem';

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

describe('<SmartInventoryHostListItem />', () => {
  let wrapper;

  beforeEach(() => {
    wrapper = mountWithContexts(
      <SmartInventoryHostListItem
        detailUrl="/inventories/smart_inventory/1/hosts/2"
        host={mockHost}
        isSelected={false}
        onSelect={() => {}}
      />
    );
  });

  afterEach(() => {
    wrapper.unmount();
  });

  test('should render expected row cells', () => {
    const cells = wrapper.find('DataListCell');
    expect(cells).toHaveLength(3);
    expect(cells.at(0).text()).toEqual('Host Two');
    expect(cells.at(1).find('Sparkline').length).toEqual(1);
    expect(cells.at(2).text()).toContain('Inv 1');
  });
});
