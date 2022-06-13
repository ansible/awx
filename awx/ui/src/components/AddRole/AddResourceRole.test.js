/* eslint-disable react/jsx-pascal-case */
import React from 'react';
import { shallow } from 'enzyme';
import { createMemoryHistory } from 'history';
import { act } from 'react-dom/test-utils';

import { TeamsAPI, UsersAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import AddResourceRole, { _AddResourceRole } from './AddResourceRole';

jest.mock('../../api/models/Teams');
jest.mock('../../api/models/Users');

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useHistory: () => ({ push: jest.fn(), location: { pathname: {} } }),
}));
// TODO: Once error handling is functional in
// this component write tests for it

describe('<_AddResourceRole />', () => {
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

  beforeEach(() => {
    UsersAPI.read.mockResolvedValue({
      data: {
        count: 2,
        results: [
          { id: 1, username: 'foo', url: '' },
          { id: 2, username: 'bar', url: '' },
          { id: 3, username: 'baz', url: '' },
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
  });

  test('initially renders without crashing', () => {
    shallow(
      <_AddResourceRole
        onClose={() => {}}
        onSave={() => {}}
        roles={roles}
        i18n={{ _: (val) => val.toString() }}
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
    await waitForElement(wrapper, 'EmptyStateBody', (el) => el.length === 0);
    expect(wrapper.find('Chip').length).toBe(0);
    wrapper.find('CheckboxListItem[name="foo"]').invoke('onSelect')(true);
    wrapper.find('CheckboxListItem[name="bar"]').invoke('onSelect')(true);
    wrapper.find('CheckboxListItem[name="baz"]').invoke('onSelect')(true);
    wrapper.find('CheckboxListItem[name="baz"]').invoke('onSelect')(false);
    expect(
      wrapper.find('CheckboxListItem[name="foo"]').prop('isSelected')
    ).toBe(true);
    expect(
      wrapper.find('CheckboxListItem[name="bar"]').prop('isSelected')
    ).toBe(true);
    expect(
      wrapper.find('CheckboxListItem[name="baz"]').prop('isSelected')
    ).toBe(false);
    expect(wrapper.find('Chip').length).toBe(2);
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
    expect(UsersAPI.associateRole).toBeCalledWith(2, 1);
    expect(UsersAPI.associateRole).toBeCalledTimes(2);
  });

  test('should call on error properly', async () => {
    let wrapper;
    const onError = jest.fn();
    UsersAPI.associateRole.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'post',
            url: '/api/v2/users',
          },
          data: 'An error occurred',
          status: 403,
        },
      })
    );
    act(() => {
      wrapper = mountWithContexts(
        <AddResourceRole
          onClose={() => {}}
          onError={onError}
          onSave={() => {}}
          roles={roles}
        />,
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
    await waitForElement(wrapper, 'EmptyStateBody', (el) => el.length === 0);
    act(() =>
      wrapper.find('CheckboxListItem[name="foo"]').invoke('onSelect')(true)
    );
    wrapper.update();
    expect(
      wrapper.find('CheckboxListItem[name="foo"]').prop('isSelected')
    ).toBe(true);
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
    expect(onError).toBeCalled();
  });

  test('should update history properly', async () => {
    let wrapper;
    const history = createMemoryHistory({
      initialEntries: ['organizations/2/access?resource.order_by=-username'],
    });
    act(() => {
      wrapper = mountWithContexts(
        <AddResourceRole onClose={() => {}} onSave={() => {}} roles={roles} />,
        { context: { router: { history } } }
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
    await waitForElement(wrapper, 'EmptyStateBody', (el) => el.length === 0);
    act(() =>
      wrapper.find('CheckboxListItem[name="foo"]').invoke('onSelect')(true)
    );
    wrapper.update();
    expect(
      wrapper.find('CheckboxListItem[name="foo"]').prop('isSelected')
    ).toBe(true);
    await act(async () =>
      wrapper.find('PFWizard').prop('onGoToStep')({ id: 1 })
    );
    wrapper.update();
    expect(history.location.pathname).toEqual('organizations/2/access');
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
      (el) => el.prop('isSelected') === true
    );
    act(() => wrapper.find('SelectableCard[label="Teams"]').prop('onClick')());
    wrapper.update();

    await waitForElement(
      wrapper,
      'SelectableCard[label="Teams"]',
      (el) => el.prop('isSelected') === true
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
    await waitForElement(wrapper, 'EmptyStateBody', (el) => el.length === 0);
    act(() =>
      wrapper.find('CheckboxListItem[name="foo"]').invoke('onSelect')(true)
    );
    wrapper.update();
    expect(
      wrapper.find('CheckboxListItem[name="foo"]').prop('isSelected')
    ).toBe(true);
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
    await waitForElement(wrapper, 'EmptyStateBody', (el) => el.length === 0);
    wrapper
      .find('DataListCheck')
      .map((item) => expect(item.prop('checked')).toBe(false));
    act(() => wrapper.find('Button[type="submit"]').prop('onClick')());
    wrapper.update();

    // Make sure that no roles have been selected
    wrapper
      .find('Checkbox')
      .map((card) => expect(card.prop('isChecked')).toBe(false));

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
  test('should show correct button text', async () => {
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
    expect(wrapper.find('Button[type="submit"]').text()).toBe('Next');

    wrapper.update();

    // Step 2
    await waitForElement(wrapper, 'EmptyStateBody', (el) => el.length === 0);
    expect(wrapper.find('Chip').length).toBe(0);
    act(() =>
      wrapper.find('CheckboxListItem[name="foo"]').invoke('onSelect')(true)
    );
    wrapper.update();
    expect(
      wrapper.find('CheckboxListItem[name="foo"]').prop('isSelected')
    ).toBe(true);
    expect(wrapper.find('Chip').length).toBe(1);
    expect(wrapper.find('Button[type="submit"]').text()).toBe('Next');
    act(() => wrapper.find('Button[type="submit"]').prop('onClick')());
    wrapper.update();

    // Step 3
    act(() =>
      wrapper.find('Checkbox[aria-label="Admin"]').invoke('onChange')(true)
    );
    expect(wrapper.find('Button[type="submit"]').text()).toBe('Save');
    wrapper.update();

    // Go Back
    await act(async () =>
      wrapper.find('Button[variant="secondary"]').prop('onClick')()
    );
    wrapper.update();
    expect(wrapper.find('Button[type="submit"]').text()).toBe('Next');

    // return to last step
    await act(async () =>
      wrapper.find('Button[type="submit"]').prop('onClick')()
    );
    wrapper.update();
    expect(wrapper.find('Button[type="submit"]').text()).toBe('Save');
  });
});
