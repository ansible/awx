import React from 'react';
import { mountWithContexts } from '../../../../enzymeHelpers';
import OrganizationNotifications from '../../../../../src/pages/Organizations/screens/Organization/OrganizationNotifications';
import { sleep } from '../../../../testUtils';
import { OrganizationsAPI } from '../../../../../src/api';

jest.mock('../../../../../src/api');

describe('<OrganizationNotifications />', () => {
  let data;

  beforeEach(() => {
    data = {
      count: 2,
      results: [{
        id: 1,
        name: 'Notification one',
        url: '/api/v2/notification_templates/1/',
        notification_type: 'email',
      }, {
        id: 2,
        name: 'Notification two',
        url: '/api/v2/notification_templates/2/',
        notification_type: 'email',
      }]
    };
    OrganizationsAPI.readNotificationTemplates.mockReturnValue({ data });
    OrganizationsAPI.readNotificationTemplatesSuccess.mockReturnValue({
      data: { results: [{ id: 1 }] },
    });
    OrganizationsAPI.readNotificationTemplatesError.mockReturnValue({
      data: { results: [{ id: 2 }] },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('initially renders succesfully', async () => {
    const wrapper = mountWithContexts(
      <OrganizationNotifications id={1} canToggleNotifications />
    );
    await sleep(0);
    wrapper.update();
    expect(wrapper).toMatchSnapshot();
  });

  test('should render list fetched of items', async () => {
    const wrapper = mountWithContexts(
      <OrganizationNotifications id={1} canToggleNotifications />
    );
    await sleep(0);
    wrapper.update();

    expect(OrganizationsAPI.readNotificationTemplates).toHaveBeenCalled();
    expect(wrapper.find('OrganizationNotifications').state('notifications'))
      .toEqual(data.results);
    const items = wrapper.find('NotificationListItem');
    expect(items).toHaveLength(2);
    expect(items.at(0).prop('successTurnedOn')).toEqual(true);
    expect(items.at(0).prop('errorTurnedOn')).toEqual(false);
    expect(items.at(1).prop('successTurnedOn')).toEqual(false);
    expect(items.at(1).prop('errorTurnedOn')).toEqual(true);
  });

  test('should enable success notification', async () => {
    const wrapper = mountWithContexts(
      <OrganizationNotifications id={1} canToggleNotifications />
    );
    await sleep(0);
    wrapper.update();

    expect(
      wrapper.find('OrganizationNotifications').state('successTemplateIds')
    ).toEqual([1]);
    const items = wrapper.find('NotificationListItem');
    items.at(1).find('Switch').at(0).prop('onChange')();
    expect(OrganizationsAPI.updateNotificationTemplateAssociation).toHaveBeenCalledWith(1, 2, 'success', true);
    await sleep(0);
    wrapper.update();
    expect(
      wrapper.find('OrganizationNotifications').state('successTemplateIds')
    ).toEqual([1, 2]);
  });

  test('should enable error notification', async () => {
    const wrapper = mountWithContexts(
      <OrganizationNotifications id={1} canToggleNotifications />
    );
    await sleep(0);
    wrapper.update();

    expect(
      wrapper.find('OrganizationNotifications').state('errorTemplateIds')
    ).toEqual([2]);
    const items = wrapper.find('NotificationListItem');
    items.at(0).find('Switch').at(1).prop('onChange')();
    expect(OrganizationsAPI.updateNotificationTemplateAssociation).toHaveBeenCalledWith(1, 1, 'error', true);
    await sleep(0);
    wrapper.update();
    expect(
      wrapper.find('OrganizationNotifications').state('errorTemplateIds')
    ).toEqual([2, 1]);
  });

  test('should disable success notification', async () => {
    const wrapper = mountWithContexts(
      <OrganizationNotifications id={1} canToggleNotifications />
    );
    await sleep(0);
    wrapper.update();

    expect(
      wrapper.find('OrganizationNotifications').state('successTemplateIds')
    ).toEqual([1]);
    const items = wrapper.find('NotificationListItem');
    items.at(0).find('Switch').at(0).prop('onChange')();
    expect(OrganizationsAPI.updateNotificationTemplateAssociation).toHaveBeenCalledWith(1, 1, 'success', false);
    await sleep(0);
    wrapper.update();
    expect(
      wrapper.find('OrganizationNotifications').state('successTemplateIds')
    ).toEqual([]);
  });

  test('should disable error notification', async () => {
    const wrapper = mountWithContexts(
      <OrganizationNotifications id={1} canToggleNotifications />
    );
    await sleep(0);
    wrapper.update();

    expect(
      wrapper.find('OrganizationNotifications').state('errorTemplateIds')
    ).toEqual([2]);
    const items = wrapper.find('NotificationListItem');
    items.at(1).find('Switch').at(1).prop('onChange')();
    expect(OrganizationsAPI.updateNotificationTemplateAssociation).toHaveBeenCalledWith(1, 2, 'error', false);
    await sleep(0);
    wrapper.update();
    expect(
      wrapper.find('OrganizationNotifications').state('errorTemplateIds')
    ).toEqual([]);
  });
});
