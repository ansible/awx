import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import InventoryRelatedGroupListItem from './InventoryRelatedGroupListItem';
import mockRelatedGroups from '../shared/data.relatedGroups.json';

jest.mock('../../../api');

describe('<InventoryRelatedGroupListItem />', () => {
  let wrapper;
  const mockGroup = mockRelatedGroups.results[0];

  beforeEach(() => {
    wrapper = mountWithContexts(
      <InventoryRelatedGroupListItem
        detailUrl="/group/1"
        editUrl="/group/1"
        group={mockGroup}
        isSelected={false}
        onSelect={() => {}}
      />
    );
  });

  afterEach(() => {
    wrapper.unmount();
  });

  test('should display expected row item content', () => {
    expect(
      wrapper
        .find('DataListCell')
        .first()
        .text()
    ).toBe(' Group 2 Inventory 0');
  });

  test('edit button shown to users with edit capabilities', () => {
    expect(wrapper.find('PencilAltIcon').exists()).toBeTruthy();
  });

  test('edit button hidden from users without edit capabilities', () => {
    wrapper = mountWithContexts(
      <InventoryRelatedGroupListItem
        detailUrl="/group/1"
        editUrl="/group/1"
        group={mockRelatedGroups.results[2]}
        isSelected={false}
        onSelect={() => {}}
      />
    );
    expect(wrapper.find('PencilAltIcon').exists()).toBeFalsy();
  });
});
