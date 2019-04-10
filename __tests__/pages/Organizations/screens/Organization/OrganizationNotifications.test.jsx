import React from 'react';
import { mount } from 'enzyme';
import { MemoryRouter } from 'react-router-dom';
import OrganizationNotifications from '../../../../../src/pages/Organizations/screens/Organization/OrganizationNotifications';

describe('<OrganizationNotifications />', () => {
  test('initially renders succesfully', () => {
    mount(
      <MemoryRouter initialEntries={['/organizations/1']} initialIndex={0}>
        <OrganizationNotifications
          match={{ path: '/organizations/:id/notifications', url: '/organizations/1/notifications' }}
          location={{ search: '', pathname: '/organizations/1/notifications' }}
          params={{}}
          api={{
            getOrganizationNotifications: jest.fn(),
            getOrganizationNotificationSuccess: jest.fn(),
            getOrganizationNotificationError: jest.fn(),
            createOrganizationNotificationSuccess: jest.fn(),
            createOrganizationNotificationError: jest.fn()
          }}
        />
      </MemoryRouter>
    );
  });
  test('handles api requests', () => {
    const getOrganizationNotifications = jest.fn();
    const getOrganizationNotificationSuccess = jest.fn();
    const getOrganizationNotificationError = jest.fn();
    const createOrganizationNotificationSuccess = jest.fn();
    const createOrganizationNotificationError = jest.fn();
    const wrapper = mount(
      <MemoryRouter initialEntries={['/organizations/1']} initialIndex={0}>
        <OrganizationNotifications
          match={{ path: '/organizations/:id/notifications', url: '/organizations/1/notifications' }}
          location={{ search: '', pathname: '/organizations/1/notifications' }}
          params={{}}
          api={{
            getOrganizationNotifications,
            getOrganizationNotificationSuccess,
            getOrganizationNotificationError,
            createOrganizationNotificationSuccess,
            createOrganizationNotificationError
          }}
        />
      </MemoryRouter>
    ).find('OrganizationNotifications');
    wrapper.instance().readOrgNotifications(1, { foo: 'bar' });
    expect(getOrganizationNotifications).toHaveBeenCalledWith(1, { foo: 'bar' });
    wrapper.instance().readOrgNotificationSuccess(1, { foo: 'bar' });
    expect(getOrganizationNotificationSuccess).toHaveBeenCalledWith(1, { foo: 'bar' });
    wrapper.instance().readOrgNotificationError(1, { foo: 'bar' });
    expect(getOrganizationNotificationError).toHaveBeenCalledWith(1, { foo: 'bar' });
    wrapper.instance().createOrgNotificationSuccess(1, { id: 2 });
    expect(createOrganizationNotificationSuccess).toHaveBeenCalledWith(1, { id: 2 });
    wrapper.instance().createOrgNotificationError(1, { id: 2 });
    expect(createOrganizationNotificationError).toHaveBeenCalledWith(1, { id: 2 });
  });
});
