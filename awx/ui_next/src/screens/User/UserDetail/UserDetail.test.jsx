import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import { UsersAPI } from '../../../api';
import UserDetail from './UserDetail';
import mockDetails from '../data.user.json';

jest.mock('../../../api');

describe('<UserDetail />', () => {
  test('initially renders successfully', () => {
    mountWithContexts(<UserDetail user={mockDetails} />);
  });

  test('should render Details', () => {
    const wrapper = mountWithContexts(<UserDetail user={mockDetails} />);
    function assertDetail(label, value) {
      expect(wrapper.find(`Detail[label="${label}"] dt`).text()).toBe(label);
      expect(wrapper.find(`Detail[label="${label}"] dd`).text()).toBe(value);
    }

    assertDetail('Username', mockDetails.username);
    assertDetail('Email', mockDetails.email);
    assertDetail('First Name', mockDetails.first_name);
    assertDetail('Last Name', mockDetails.last_name);
    assertDetail('User Type', 'System Administrator');
    assertDetail('Last Login', `11/4/2019, 11:12:36 PM`);
    assertDetail('Created', `10/28/2019, 3:01:07 PM`);
    assertDetail('Type', `SOCIAL`);
  });

  test('User Type Detail should render expected strings', async () => {
    let wrapper;
    wrapper = mountWithContexts(
      <UserDetail
        user={{
          ...mockDetails,
          is_superuser: false,
          is_system_auditor: true,
        }}
      />
    );
    expect(wrapper.find(`Detail[label="User Type"] dd`).text()).toBe(
      'System Auditor'
    );

    wrapper = mountWithContexts(
      <UserDetail
        user={{
          ...mockDetails,
          is_superuser: false,
          is_system_auditor: false,
        }}
      />
    );
    expect(wrapper.find(`Detail[label="User Type"] dd`).text()).toBe(
      'Normal User'
    );
  });

  test('should show edit button for users with edit permission', async () => {
    const wrapper = mountWithContexts(<UserDetail user={mockDetails} />);
    const editButton = await waitForElement(
      wrapper,
      'UserDetail Button[aria-label="edit"]'
    );
    expect(editButton.text()).toEqual('Edit');
    expect(editButton.prop('to')).toBe(`/users/${mockDetails.id}/edit`);
  });

  test('should hide edit button for users without edit permission', async () => {
    const wrapper = mountWithContexts(
      <UserDetail
        user={{
          ...mockDetails,
          summary_fields: {
            user_capabilities: {
              edit: false,
            },
          },
        }}
      />
    );
    await waitForElement(wrapper, 'UserDetail');
    expect(wrapper.find('UserDetail Button[aria-label="edit"]').length).toBe(0);
  });

  test('edit button should navigate to user edit', () => {
    const history = createMemoryHistory();
    const wrapper = mountWithContexts(<UserDetail user={mockDetails} />, {
      context: { router: { history } },
    });
    expect(wrapper.find('Button[aria-label="edit"]').length).toBe(1);
    wrapper
      .find('Button[aria-label="edit"] Link')
      .simulate('click', { button: 0 });
    expect(history.location.pathname).toEqual('/users/1/edit');
  });

  test('expected api call is made for delete', async () => {
    const wrapper = mountWithContexts(<UserDetail user={mockDetails} />);
    await waitForElement(wrapper, 'UserDetail Button[aria-label="Delete"]');
    await act(async () => {
      wrapper.find('DeleteButton').invoke('onConfirm')();
    });
    expect(UsersAPI.destroy).toHaveBeenCalledTimes(1);
  });

  test('Error dialog shown for failed deletion', async () => {
    UsersAPI.destroy.mockImplementationOnce(() => Promise.reject(new Error()));
    const wrapper = mountWithContexts(<UserDetail user={mockDetails} />);
    await waitForElement(wrapper, 'UserDetail Button[aria-label="Delete"]');
    await act(async () => {
      wrapper.find('DeleteButton').invoke('onConfirm')();
    });
    await waitForElement(
      wrapper,
      'Modal[title="Error!"]',
      el => el.length === 1
    );
    await act(async () => {
      wrapper.find('Modal[title="Error!"]').invoke('onClose')();
    });
    await waitForElement(
      wrapper,
      'Modal[title="Error!"]',
      el => el.length === 0
    );
  });
});
