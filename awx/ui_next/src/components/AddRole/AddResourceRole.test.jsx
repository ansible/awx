/* eslint-disable react/jsx-pascal-case */
import React from 'react';
import { shallow } from 'enzyme';
import { act } from 'react-dom/test-utils';

import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import AddResourceRole, { _AddResourceRole } from './AddResourceRole';
import { TeamsAPI, UsersAPI } from '../../api';

jest.mock('../../api/models/Teams');
jest.mock('../../api/models/Users');

// TODO: Once error handling is functional in
// this component write tests for it

describe('<_AddResourceRole />', () => {
  UsersAPI.read.mockResolvedValue({
    data: {
      count: 2,
      results: [
        { id: 1, username: 'foo', url: '' },
        { id: 2, username: 'bar', url: '' },
      ],
    },
  });
  UsersAPI.readOptions.mockResolvedValue({
    data: { related: {}, actions: { GET: {} } },
  });
  TeamsAPI.read.mockResolvedValue({
    data: {
      count: 2,
      results: [
        { id: 1, name: 'Team foo', url: '' },
        { id: 2, name: 'Team bar', url: '' },
      ],
    },
  });
  TeamsAPI.readOptions.mockResolvedValue({
    data: { related: {}, actions: { GET: {} } },
  });
  const roles = {
    admin_role: {
      description: 'Can manage all aspects of the organization',
      id: 1,
      name: 'Admin',
    },
    execute_role: {
      description: 'May run any executable resources in the organization',
      id: 2,
      name: 'Execute',
    },
  };
  test('initially renders without crashing', () => {
    shallow(
      <_AddResourceRole
        onClose={() => {}}
        onSave={() => {}}
        roles={roles}
        i18n={{ _: val => val.toString() }}
      />
    );
  });
  test('should save properly', async () => {
    let wrapper;
    act(() => {
      wrapper = mountWithContexts(
        <AddResourceRole onClose={() => {}} onSave={() => {}} roles={roles} />,
        { context: { network: { handleHttpError: () => {} } } }
      );
    });
    wrapper.update();

    // Step 1
    const selectableCardWrapper = wrapper.find('SelectableCard');
    expect(selectableCardWrapper.length).toBe(2);
    act(() => wrapper.find('SelectableCard[label="Users"]').prop('onClick')());
    wrapper.update();
    await act(async () =>
      wrapper.find('Button[type="submit"]').prop('onClick')()
    );
    wrapper.update();

    // Step 2
    await waitForElement(wrapper, 'EmptyStateBody', el => el.length === 0);
    act(() =>
      wrapper.find('DataListCheck[name="foo"]').invoke('onChange')(true)
    );
    wrapper.update();
    expect(wrapper.find('DataListCheck[name="foo"]').prop('checked')).toBe(
      true
    );
    act(() => wrapper.find('Button[type="submit"]').prop('onClick')());
    wrapper.update();

    // Step 3
    act(() =>
      wrapper.find('Checkbox[aria-label="Admin"]').invoke('onChange')(true)
    );
    wrapper.update();
    expect(wrapper.find('Checkbox[aria-label="Admin"]').prop('isChecked')).toBe(
      true
    );

    // Save
    await act(async () =>
      wrapper.find('Button[type="submit"]').prop('onClick')()
    );
    expect(UsersAPI.associateRole).toBeCalledWith(1, 1);
  });

  test('should successfuly click user/team cards', async () => {
    let wrapper;
    act(() => {
      wrapper = mountWithContexts(
        <AddResourceRole onClose={() => {}} onSave={() => {}} roles={roles} />,
        { context: { network: { handleHttpError: () => {} } } }
      );
    });
    wrapper.update();

    const selectableCardWrapper = wrapper.find('SelectableCard');
    expect(selectableCardWrapper.length).toBe(2);
    act(() => wrapper.find('SelectableCard[label="Users"]').prop('onClick')());
    wrapper.update();

    await waitForElement(
      wrapper,
      'SelectableCard[label="Users"]',
      el => el.prop('isSelected') === true
    );
    act(() => wrapper.find('SelectableCard[label="Teams"]').prop('onClick')());
    wrapper.update();

    await waitForElement(
      wrapper,
      'SelectableCard[label="Teams"]',
      el => el.prop('isSelected') === true
    );
  });

  test('should reset values with resource type changes', async () => {
    let wrapper;
    act(() => {
      wrapper = mountWithContexts(
        <AddResourceRole onClose={() => {}} onSave={() => {}} roles={roles} />,
        { context: { network: { handleHttpError: () => {} } } }
      );
    });
    wrapper.update();

    // Step 1
    const selectableCardWrapper = wrapper.find('SelectableCard');
    expect(selectableCardWrapper.length).toBe(2);
    act(() => wrapper.find('SelectableCard[label="Users"]').prop('onClick')());
    wrapper.update();
    await act(async () =>
      wrapper.find('Button[type="submit"]').prop('onClick')()
    );
    wrapper.update();

    // Step 2
    await waitForElement(wrapper, 'EmptyStateBody', el => el.length === 0);
    act(() =>
      wrapper.find('DataListCheck[name="foo"]').invoke('onChange')(true)
    );
    wrapper.update();
    expect(wrapper.find('DataListCheck[name="foo"]').prop('checked')).toBe(
      true
    );
    act(() => wrapper.find('Button[type="submit"]').prop('onClick')());
    wrapper.update();

    // Step 3
    act(() =>
      wrapper.find('Checkbox[aria-label="Admin"]').invoke('onChange')(true)
    );
    wrapper.update();
    expect(wrapper.find('Checkbox[aria-label="Admin"]').prop('isChecked')).toBe(
      true
    );

    // Go back to step 1
    act(() => {
      wrapper
        .find('WizardNavItem[content="Select a Resource Type"]')
        .find('button')
        .prop('onClick')({ id: 1 });
    });
    wrapper.update();
    expect(
      wrapper
        .find('WizardNavItem[content="Select a Resource Type"]')
        .prop('isCurrent')
    ).toBe(true);

    // Go back to step 1 and this time select teams.  Doing so should clear following steps
    act(() => wrapper.find('SelectableCard[label="Teams"]').prop('onClick')());
    wrapper.update();
    await act(async () =>
      wrapper.find('Button[type="submit"]').prop('onClick')()
    );
    wrapper.update();

    // Make sure no teams have been selected
    await waitForElement(wrapper, 'EmptyStateBody', el => el.length === 0);
    wrapper
      .find('DataListCheck')
      .map(item => expect(item.prop('checked')).toBe(false));
    act(() => wrapper.find('Button[type="submit"]').prop('onClick')());
    wrapper.update();

    // Make sure that no roles have been selected
    wrapper
      .find('Checkbox')
      .map(card => expect(card.prop('isChecked')).toBe(false));

    // Make sure the save button is disabled
    expect(wrapper.find('Button[type="submit"]').prop('isDisabled')).toBe(true);
  });

  test('should not display team as a choice in case credential does not have organization', () => {
    const wrapper = mountWithContexts(
      <AddResourceRole
        onClose={() => {}}
        onSave={() => {}}
        roles={roles}
        resource={{ type: 'credential', organization: null }}
      />,
      { context: { network: { handleHttpError: () => {} } } }
    );

    expect(wrapper.find('SelectableCard').length).toBe(1);
    wrapper.find('SelectableCard[label="Users"]').simulate('click');
    wrapper.update();
    expect(
      wrapper.find('SelectableCard[label="Users"]').prop('isSelected')
    ).toBe(true);
  });
});
