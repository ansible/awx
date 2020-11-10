import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import UserForm from './UserForm';
import { UsersAPI } from '../../../api';
import mockData from '../data.user.json';

jest.mock('../../../api');

describe('<UserForm />', () => {
  let wrapper;

  const userOptionsResolve = {
    data: {
      actions: {
        GET: {},
        POST: {},
      },
    },
  };

  beforeEach(async () => {
    await UsersAPI.readOptions.mockImplementation(() => userOptionsResolve);
  });

  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('initially renders successfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <UserForm handleSubmit={jest.fn()} handleCancel={jest.fn()} />
      );
    });

    expect(wrapper.find('UserForm').length).toBe(1);
  });

  test('add form displays all form fields', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <UserForm handleSubmit={jest.fn()} handleCancel={jest.fn()} />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('FormGroup[label="Username"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Email"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="First Name"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Last Name"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Password"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Confirm Password"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Organization"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="User Type"]').length).toBe(1);
  });

  test('edit form hides org field', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <UserForm
          handleSubmit={jest.fn()}
          handleCancel={jest.fn()}
          user={mockData}
        />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('FormGroup[label="Organization"]').length).toBe(0);
  });

  test('inputs should update form value on change', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <UserForm handleSubmit={jest.fn()} handleCancel={jest.fn()} />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    await act(async () => {
      wrapper.find('OrganizationLookup').invoke('onBlur')();
      wrapper.find('OrganizationLookup').invoke('onChange')({
        id: 1,
        name: 'organization',
      });
    });
    wrapper.update();
    expect(wrapper.find('OrganizationLookup').prop('value')).toEqual({
      id: 1,
      name: 'organization',
    });
  });

  test('fields required on add', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <UserForm handleSubmit={jest.fn()} handleCancel={jest.fn()} />
      );
    });

    const passwordFields = wrapper.find('PasswordField');

    expect(passwordFields.length).toBe(2);
    expect(passwordFields.at(0).prop('isRequired')).toBe(true);
    expect(passwordFields.at(1).prop('isRequired')).toBe(true);

    expect(wrapper.find('FormField[label="Username"]').prop('isRequired')).toBe(
      true
    );
  });

  test('username field is required on edit', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <UserForm
          user={{ ...mockData, external_account: '', auth: [] }}
          handleSubmit={jest.fn()}
          handleCancel={jest.fn()}
        />
      );
    });

    expect(wrapper.find('FormField[label="Username"]').prop('isRequired')).toBe(
      true
    );
  });

  test('password fields are not required on edit', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <UserForm
          user={{ ...mockData, external_account: '', auth: [] }}
          handleSubmit={jest.fn()}
          handleCancel={jest.fn()}
        />
      );
    });

    const passwordFields = wrapper.find('PasswordField');

    expect(passwordFields.length).toBe(2);
    expect(passwordFields.at(0).prop('isRequired')).toBe(false);
    expect(passwordFields.at(1).prop('isRequired')).toBe(false);
  });

  test('username should not be required for external accounts', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <UserForm
          user={mockData}
          handleSubmit={jest.fn()}
          handleCancel={jest.fn()}
        />
      );
    });
    expect(wrapper.find('FormField[label="Username"]').prop('isRequired')).toBe(
      false
    );
  });

  test('username should not be required for ldap accounts', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <UserForm
          user={{
            ...mockData,
            ldap_dn:
              'uid=binduser,cn=users,cn=accounts,dc=lan,dc=example,dc=com',
          }}
          handleSubmit={jest.fn()}
          handleCancel={jest.fn()}
        />
      );
    });
    expect(wrapper.find('FormField[label="Username"]').prop('isRequired')).toBe(
      false
    );
  });

  test('password fields are not displayed for social/ldap login', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <UserForm
          user={mockData}
          handleSubmit={jest.fn()}
          handleCancel={jest.fn()}
        />
      );
    });

    const passwordFields = wrapper.find('PasswordField');

    expect(passwordFields.length).toBe(0);
  });

  test('should call handleSubmit when Submit button is clicked', async () => {
    const handleSubmit = jest.fn();
    await act(async () => {
      wrapper = mountWithContexts(
        <UserForm
          user={mockData}
          handleSubmit={handleSubmit}
          handleCancel={jest.fn()}
        />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(handleSubmit).not.toHaveBeenCalled();
    await act(async () => {
      wrapper.find('button[aria-label="Save"]').simulate('click');
    });
    expect(handleSubmit).toBeCalled();
  });

  test('should call handleCancel when Cancel button is clicked', async () => {
    const handleCancel = jest.fn();
    await act(async () => {
      wrapper = mountWithContexts(
        <UserForm
          user={mockData}
          handleSubmit={jest.fn()}
          handleCancel={handleCancel}
        />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(handleCancel).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    expect(handleCancel).toBeCalled();
  });
});
