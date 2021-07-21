import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import HostGroupItem from './HostGroupItem';

describe('<HostGroupItem />', () => {
  let wrapper;
  const mockGroup = {
    id: 2,
    type: 'group',
    name: 'foo',
    inventory: 1,
    summary_fields: {
      user_capabilities: {
        edit: true,
      },
    },
  };

  beforeEach(() => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <HostGroupItem
            group={mockGroup}
            inventoryId={1}
            isSelected={false}
            onSelect={() => {}}
          />
        </tbody>
      </table>
    );
  });

  test('initially renders successfully', () => {
    expect(wrapper.find('HostGroupItem').length).toBe(1);
  });

  test('edit button should be shown to users with edit capabilities', () => {
    expect(wrapper.find('PencilAltIcon').exists()).toBeTruthy();
  });

  test('edit button should be hidden from users without edit capabilities', () => {
    const copyMockGroup = { ...mockGroup };
    copyMockGroup.summary_fields.user_capabilities.edit = false;

    wrapper = mountWithContexts(
      <table>
        <tbody>
          <HostGroupItem
            group={copyMockGroup}
            inventoryId={1}
            isSelected={false}
            onSelect={() => {}}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('PencilAltIcon').exists()).toBeFalsy();
  });
});
