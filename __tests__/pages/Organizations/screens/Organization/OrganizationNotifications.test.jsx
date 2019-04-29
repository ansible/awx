import React from 'react';
import { mountWithContexts } from '../../../../enzymeHelpers';
import OrganizationNotifications from '../../../../../src/pages/Organizations/screens/Organization/OrganizationNotifications';
import { sleep } from '../../../../testUtils';

describe('<OrganizationNotifications />', () => {
  let data;
  let network;

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
    network = {
      api: {
        getOrganizationNotifications: jest.fn()
          .mockReturnValue(Promise.resolve({ data })),
        getOrganizationNotificationSuccess: jest.fn()
          .mockReturnValue(Promise.resolve({
            data: { results: [{ id: 1 }] },
          })),
        getOrganizationNotificationError: jest.fn()
          .mockReturnValue(Promise.resolve({
            data: { results: [{ id: 2 }] },
          })),
        createOrganizationNotificationSuccess: jest.fn(),
        createOrganizationNotificationError: jest.fn(),
        toJSON: () => '/api/',
      }
    };
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('initially renders succesfully', async () => {
    const wrapper = mountWithContexts(
      <OrganizationNotifications id={1} canToggleNotifications />,
      { context: { network } }
    );
    await sleep(0);
    wrapper.update();
    expect(wrapper).toMatchSnapshot();
  });

  test('should render list fetched of items', async () => {
    const wrapper = mountWithContexts(
      <OrganizationNotifications id={1} canToggleNotifications />,
      {
        context: { network }
      }
    );
    await sleep(0);
    wrapper.update();

    expect(network.api.getOrganizationNotifications).toHaveBeenCalled();
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
      <OrganizationNotifications id={1} canToggleNotifications />,
      {
        context: { network }
      }
    );
    await sleep(0);
    wrapper.update();

    expect(
      wrapper.find('OrganizationNotifications').state('successTemplateIds')
    ).toEqual([1]);
    const items = wrapper.find('NotificationListItem');
    items.at(1).find('Switch').at(0).prop('onChange')();
    expect(network.api.createOrganizationNotificationSuccess).toHaveBeenCalled();
    await sleep(0);
    wrapper.update();
    expect(
      wrapper.find('OrganizationNotifications').state('successTemplateIds')
    ).toEqual([1, 2]);
  });

  test('should enable error notification', async () => {
    const wrapper = mountWithContexts(
      <OrganizationNotifications id={1} canToggleNotifications />,
      {
        context: { network }
      }
    );
    await sleep(0);
    wrapper.update();

    expect(
      wrapper.find('OrganizationNotifications').state('errorTemplateIds')
    ).toEqual([2]);
    const items = wrapper.find('NotificationListItem');
    items.at(0).find('Switch').at(1).prop('onChange')();
    expect(network.api.createOrganizationNotificationError).toHaveBeenCalled();
    await sleep(0);
    wrapper.update();
    expect(
      wrapper.find('OrganizationNotifications').state('errorTemplateIds')
    ).toEqual([2, 1]);
  });

  test('should disable success notification', async () => {
    const wrapper = mountWithContexts(
      <OrganizationNotifications id={1} canToggleNotifications />,
      {
        context: { network }
      }
    );
    await sleep(0);
    wrapper.update();

    expect(
      wrapper.find('OrganizationNotifications').state('successTemplateIds')
    ).toEqual([1]);
    const items = wrapper.find('NotificationListItem');
    items.at(0).find('Switch').at(0).prop('onChange')();
    expect(network.api.createOrganizationNotificationSuccess).toHaveBeenCalled();
    await sleep(0);
    wrapper.update();
    expect(
      wrapper.find('OrganizationNotifications').state('successTemplateIds')
    ).toEqual([]);
  });

  test('should disable error notification', async () => {
    const wrapper = mountWithContexts(
      <OrganizationNotifications id={1} canToggleNotifications />,
      {
        context: { network }
      }
    );
    await sleep(0);
    wrapper.update();

    expect(
      wrapper.find('OrganizationNotifications').state('errorTemplateIds')
    ).toEqual([2]);
    const items = wrapper.find('NotificationListItem');
    items.at(1).find('Switch').at(1).prop('onChange')();
    expect(network.api.createOrganizationNotificationError).toHaveBeenCalled();
    await sleep(0);
    wrapper.update();
    expect(
      wrapper.find('OrganizationNotifications').state('errorTemplateIds')
    ).toEqual([]);
  });
});
