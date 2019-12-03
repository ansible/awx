import React from 'react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import AddDropDownButton from './AddDropDownButton';

describe('<AddDropDownButton />', () => {
  const dropdownItems = [
    {
      key: 'inventory',
      label: 'Inventory',
      url: `inventory/inventory/add/`,
    },
  ];
  test('should be closed initially', () => {
    const wrapper = mountWithContexts(
      <AddDropDownButton dropdownItems={dropdownItems} />
    );
    expect(wrapper.find('Dropdown').prop('isOpen')).toEqual(false);
  });

  test('should render two links', () => {
    const wrapper = mountWithContexts(
      <AddDropDownButton dropdownItems={dropdownItems} />
    );
    wrapper.find('button').simulate('click');
    expect(wrapper.find('Dropdown').prop('isOpen')).toEqual(true);
    expect(wrapper.find('Link')).toHaveLength(dropdownItems.length);
  });

  test('should close when button re-clicked', () => {
    const wrapper = mountWithContexts(
      <AddDropDownButton dropdownItems={dropdownItems} />
    );
    wrapper.find('button').simulate('click');
    expect(wrapper.find('Dropdown').prop('isOpen')).toEqual(true);
    wrapper.find('button').simulate('click');
    expect(wrapper.find('Dropdown').prop('isOpen')).toEqual(false);
  });
});
