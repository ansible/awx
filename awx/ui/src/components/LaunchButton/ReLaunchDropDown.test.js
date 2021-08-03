import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import ReLaunchDropDown from './ReLaunchDropDown';

describe('ReLaunchDropDown', () => {
  const handleRelaunch = jest.fn();

  test('expected content is rendered on initialization', () => {
    const wrapper = mountWithContexts(
      <ReLaunchDropDown handleRelaunch={handleRelaunch} />
    );

    expect(wrapper.find('Dropdown')).toHaveLength(1);
  });

  test('dropdown have expected items and callbacks', () => {
    const wrapper = mountWithContexts(
      <ReLaunchDropDown handleRelaunch={handleRelaunch} />
    );
    expect(wrapper.find('DropdownItem')).toHaveLength(0);
    wrapper.find('button').simulate('click');
    wrapper.update();
    expect(wrapper.find('DropdownItem')).toHaveLength(3);

    wrapper
      .find('DropdownItem[aria-label="Relaunch failed hosts"]')
      .simulate('click');
    expect(handleRelaunch).toHaveBeenCalledWith({ hosts: 'failed' });

    wrapper
      .find('DropdownItem[aria-label="Relaunch all hosts"]')
      .simulate('click');
    expect(handleRelaunch).toHaveBeenCalledWith({ hosts: 'all' });
  });

  test('dropdown isPrimary have expected items and callbacks', () => {
    const wrapper = mountWithContexts(
      <ReLaunchDropDown isPrimary handleRelaunch={handleRelaunch} />
    );
    expect(wrapper.find('DropdownItem')).toHaveLength(0);
    wrapper.find('button').simulate('click');
    wrapper.update();
    expect(wrapper.find('DropdownItem')).toHaveLength(3);

    wrapper
      .find('DropdownItem[aria-label="Relaunch failed hosts"]')
      .simulate('click');
    expect(handleRelaunch).toHaveBeenCalledWith({ hosts: 'failed' });

    wrapper
      .find('DropdownItem[aria-label="Relaunch all hosts"]')
      .simulate('click');
    expect(handleRelaunch).toHaveBeenCalledWith({ hosts: 'all' });
  });
});
