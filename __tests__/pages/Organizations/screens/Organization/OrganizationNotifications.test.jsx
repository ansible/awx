import React from 'react';
import { mountWithContexts } from '../../../../enzymeHelpers';

import OrganizationNotifications from '../../../../../src/pages/Organizations/screens/Organization/OrganizationNotifications';

describe('<OrganizationNotifications />', () => {
  let api;

  beforeEach(() => {
    api = {
      getOrganizationNotifications: jest.fn(),
      getOrganizationNotificationSuccess: jest.fn(),
      getOrganizationNotificationError: jest.fn(),
      createOrganizationNotificationSuccess: jest.fn(),
      createOrganizationNotificationError: jest.fn()
    };
  });

  test('initially renders succesfully', () => {
    mountWithContexts(
      <OrganizationNotifications />, { context: { network: {
        api,
        handleHttpError: () => {}
      } } }
    );
  });
  test('handles api requests', () => {
    const wrapper = mountWithContexts(
      <OrganizationNotifications />, { context: { network: {
        api,
        handleHttpError: () => {}
      } } }
    ).find('OrganizationNotifications');
    wrapper.instance().readOrgNotifications(1, { foo: 'bar' });
    expect(api.getOrganizationNotifications).toHaveBeenCalledWith(1, { foo: 'bar' });
    wrapper.instance().readOrgNotificationSuccess(1, { foo: 'bar' });
    expect(api.getOrganizationNotificationSuccess).toHaveBeenCalledWith(1, { foo: 'bar' });
    wrapper.instance().readOrgNotificationError(1, { foo: 'bar' });
    expect(api.getOrganizationNotificationError).toHaveBeenCalledWith(1, { foo: 'bar' });
    wrapper.instance().createOrgNotificationSuccess(1, { id: 2 });
    expect(api.createOrganizationNotificationSuccess).toHaveBeenCalledWith(1, { id: 2 });
    wrapper.instance().createOrgNotificationError(1, { id: 2 });
    expect(api.createOrganizationNotificationError).toHaveBeenCalledWith(1, { id: 2 });
  });
});
