import React from 'react';
import { DropdownItem } from '@patternfly/react-core';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import AddDropDownButton from './AddDropDownButton';

describe('<AddDropDownButton />', () => {
  const dropdownItems = [
    <DropdownItem key="add">Add</DropdownItem>,
    <DropdownItem key="route">Route</DropdownItem>,
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
    expect(wrapper.find('DropdownItem')).toHaveLength(dropdownItems.length);
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
