import React from 'react';
import { createMemoryHistory } from 'history';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import UserDetail from './UserDetail';
import mockDetails from '../data.user.json';

describe('<UserDetail />', () => {
  test('initially renders succesfully', () => {
    mountWithContexts(<UserDetail user={mockDetails} />);
  });

  test('should render Details', () => {
    const wrapper = mountWithContexts(<UserDetail user={mockDetails} />, {
      context: {
        linguiPublisher: {
          i18n: {
            _: key => {
              if (key.values) {
                Object.entries(key.values).forEach(([k, v]) => {
                  key.id = key.id.replace(new RegExp(`\\{${k}\\}`), v);
                });
              }
              return key.id;
            },
          },
        },
      },
    });
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
  });

  test('should show edit button for users with edit permission', async done => {
    const wrapper = mountWithContexts(<UserDetail user={mockDetails} />);
    const editButton = await waitForElement(
      wrapper,
      'UserDetail Button[aria-label="edit"]'
    );
    expect(editButton.text()).toEqual('Edit');
    expect(editButton.prop('to')).toBe(`/users/${mockDetails.id}/edit`);
    done();
  });

  test('should hide edit button for users without edit permission', async done => {
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
    done();
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
});
