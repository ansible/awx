import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import HostListItem from './HostListItem';

describe('HostListItem', () => {
  let wrapper;
  const mockInventory = {
    id: 1,
    type: 'inventory',
    name: 'Foo',
    description: 'Buzz',
    summary_fields: {
      inventory: {
        name: 'Bar',
      },
    },
  };
  test('initially renders successfully', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <HostListItem item={mockInventory} />
        </tbody>
      </table>
    );
    expect(wrapper.find('HostListItem').length).toBe(1);
    expect(wrapper.find('Td').at(0).text()).toBe('Foo');
    expect(wrapper.find('Td').at(1).text()).toBe('Buzz');
    expect(wrapper.find('Td').at(2).text()).toBe('Bar');
  });
});
