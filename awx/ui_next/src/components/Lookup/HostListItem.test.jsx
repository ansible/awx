import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import HostListItem from './HostListItem';

describe('HostListItem', () => {
  let wrapper;
  const mockInventory = {
    id: 1,
    type: 'inventory',
    name: 'Foo',
    summary_fields: {
      inventory: {
        name: 'Bar',
      },
    },
  };
  test('initially renders successfully', () => {
    wrapper = mountWithContexts(<HostListItem item={mockInventory} />);
    expect(wrapper.find('HostListItem').length).toBe(1);
    expect(wrapper.find('DataListCell[aria-label="name"]').text()).toBe('Foo');
    expect(wrapper.find('DataListCell[aria-label="inventory"]').text()).toBe(
      'Bar'
    );
  });
});
