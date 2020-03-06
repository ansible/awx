import React from 'react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import AddHostDropdown from './AddHostDropdown';

describe('<AddHostDropdown />', () => {
  let wrapper;
  let dropdownToggle;
  const onAddNew = jest.fn();
  const onAddExisting = jest.fn();

  beforeEach(() => {
    wrapper = mountWithContexts(
      <AddHostDropdown onAddNew={onAddNew} onAddExisting={onAddExisting} />
    );
    dropdownToggle = wrapper.find('DropdownToggle button');
  });

  test('should initially render a closed dropdown', () => {
    expect(wrapper.find('DropdownItem').length).toBe(0);
  });

  test('should render two dropdown items', () => {
    dropdownToggle.simulate('click');
    expect(wrapper.find('DropdownItem').length).toBe(2);
  });

  test('should close when button re-clicked', () => {
    dropdownToggle.simulate('click');
    expect(wrapper.find('DropdownItem').length).toBe(2);
    dropdownToggle.simulate('click');
    expect(wrapper.find('DropdownItem').length).toBe(0);
  });
});
