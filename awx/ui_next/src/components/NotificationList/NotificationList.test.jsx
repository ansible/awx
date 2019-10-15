import React from 'react';

import { mountWithContexts } from '@testUtils/enzymeHelpers';
import { sleep } from '@testUtils/testUtils';

import { NotificationTemplatesAPI } from '@api';

import NotificationList from './NotificationList';

jest.mock('@api');

describe('<NotificationList />', () => {
  const data = {
    count: 2,
    results: [
      {
        id: 1,
        name: 'Notification one',
        url: '/api/v2/notification_templates/1/',
        notification_type: 'email',
      },
      {
        id: 2,
        name: 'Notification two',
        url: '/api/v2/notification_templates/2/',
        notification_type: 'email',
      },
      {
        id: 3,
        name: 'Notification three',
        url: '/api/v2/notification_templates/3/',
        notification_type: 'email',
      },
    ],
  };

  const MockModel = jest.fn().mockImplementation(() => {
    return {
      readNotificationTemplatesSuccess: jest.fn(),
      readNotificationTemplatesError: jest.fn(),
      readNotificationTemplatesStarted: jest.fn(),
      associateNotificationTemplate: jest.fn(),
      disassociateNotificationTemplate: jest.fn(),
    };
  });

  const MockModelAPI = new MockModel();

  NotificationTemplatesAPI.readOptions.mockReturnValue({
    data: {
      actions: {
        GET: {
          notification_type: {
            choices: [['email', 'Email']],
          },
        },
      },
    },
  });

  beforeEach(() => {
    NotificationTemplatesAPI.read.mockReturnValue({ data });
    MockModelAPI.readNotificationTemplatesSuccess.mockReturnValue({
      data: { results: [{ id: 1 }] },
    });
    MockModelAPI.readNotificationTemplatesError.mockReturnValue({
      data: { results: [{ id: 2 }] },
    });
    MockModelAPI.readNotificationTemplatesStarted.mockReturnValue({
      data: { results: [{ id: 3 }] },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('initially renders succesfully', async () => {
    const wrapper = mountWithContexts(
      <NotificationList id={1} canToggleNotifications apiModel={MockModelAPI} />
    );
    await sleep(0);
    wrapper.update();
    const dataList = wrapper.find('PaginatedDataList');
    expect(dataList).toHaveLength(1);
    expect(dataList.prop('items')).toEqual(data.results);
  });

  test('should render list fetched of items', async () => {
    const wrapper = mountWithContexts(
      <NotificationList id={1} canToggleNotifications apiModel={MockModelAPI} />
    );
    await sleep(0);
    wrapper.update();

    expect(NotificationTemplatesAPI.read).toHaveBeenCalled();
    expect(wrapper.find('NotificationList').state('notifications')).toEqual(
      data.results
    );
    const items = wrapper.find('NotificationListItem');
    expect(items).toHaveLength(3);
    expect(items.at(0).prop('successTurnedOn')).toEqual(true);
    expect(items.at(0).prop('errorTurnedOn')).toEqual(false);
    expect(items.at(0).prop('startedTurnedOn')).toEqual(false);
    expect(items.at(1).prop('successTurnedOn')).toEqual(false);
    expect(items.at(1).prop('errorTurnedOn')).toEqual(true);
    expect(items.at(1).prop('startedTurnedOn')).toEqual(false);
    expect(items.at(2).prop('successTurnedOn')).toEqual(false);
    expect(items.at(2).prop('errorTurnedOn')).toEqual(false);
    expect(items.at(2).prop('startedTurnedOn')).toEqual(true);
  });

  test('should enable success notification', async () => {
    const wrapper = mountWithContexts(
      <NotificationList id={1} canToggleNotifications apiModel={MockModelAPI} />
    );
    await sleep(0);
    wrapper.update();

    expect(
      wrapper.find('NotificationList').state('successTemplateIds')
    ).toEqual([1]);
    const items = wrapper.find('NotificationListItem');
    items
      .at(1)
      .find('Switch')
      .at(1)
      .prop('onChange')();
    expect(MockModelAPI.associateNotificationTemplate).toHaveBeenCalledWith(
      1,
      2,
      'success'
    );
    await sleep(0);
    wrapper.update();
    expect(
      wrapper.find('NotificationList').state('successTemplateIds')
    ).toEqual([1, 2]);
  });

  test('should enable error notification', async () => {
    const wrapper = mountWithContexts(
      <NotificationList id={1} canToggleNotifications apiModel={MockModelAPI} />
    );
    await sleep(0);
    wrapper.update();

    expect(wrapper.find('NotificationList').state('errorTemplateIds')).toEqual([
      2,
    ]);
    const items = wrapper.find('NotificationListItem');
    items
      .at(0)
      .find('Switch')
      .at(2)
      .prop('onChange')();
    expect(MockModelAPI.associateNotificationTemplate).toHaveBeenCalledWith(
      1,
      1,
      'error'
    );
    await sleep(0);
    wrapper.update();
    expect(wrapper.find('NotificationList').state('errorTemplateIds')).toEqual([
      2,
      1,
    ]);
  });

  test('should enable start notification', async () => {
    const wrapper = mountWithContexts(
      <NotificationList id={1} canToggleNotifications apiModel={MockModelAPI} />
    );
    await sleep(0);
    wrapper.update();

    expect(
      wrapper.find('NotificationList').state('startedTemplateIds')
    ).toEqual([3]);
    const items = wrapper.find('NotificationListItem');
    items
      .at(0)
      .find('Switch')
      .at(0)
      .prop('onChange')();
    expect(MockModelAPI.associateNotificationTemplate).toHaveBeenCalledWith(
      1,
      1,
      'started'
    );
    await sleep(0);
    wrapper.update();
    expect(
      wrapper.find('NotificationList').state('startedTemplateIds')
    ).toEqual([3, 1]);
  });

  test('should disable success notification', async () => {
    const wrapper = mountWithContexts(
      <NotificationList id={1} canToggleNotifications apiModel={MockModelAPI} />
    );
    await sleep(0);
    wrapper.update();

    expect(
      wrapper.find('NotificationList').state('successTemplateIds')
    ).toEqual([1]);
    const items = wrapper.find('NotificationListItem');
    items
      .at(0)
      .find('Switch')
      .at(1)
      .prop('onChange')();
    expect(MockModelAPI.disassociateNotificationTemplate).toHaveBeenCalledWith(
      1,
      1,
      'success'
    );
    await sleep(0);
    wrapper.update();
    expect(
      wrapper.find('NotificationList').state('successTemplateIds')
    ).toEqual([]);
  });

  test('should disable error notification', async () => {
    const wrapper = mountWithContexts(
      <NotificationList id={1} canToggleNotifications apiModel={MockModelAPI} />
    );
    await sleep(0);
    wrapper.update();

    expect(wrapper.find('NotificationList').state('errorTemplateIds')).toEqual([
      2,
    ]);
    const items = wrapper.find('NotificationListItem');
    items
      .at(1)
      .find('Switch')
      .at(2)
      .prop('onChange')();
    expect(MockModelAPI.disassociateNotificationTemplate).toHaveBeenCalledWith(
      1,
      2,
      'error'
    );
    await sleep(0);
    wrapper.update();
    expect(wrapper.find('NotificationList').state('errorTemplateIds')).toEqual(
      []
    );
  });

  test('should disable start notification', async () => {
    const wrapper = mountWithContexts(
      <NotificationList id={1} canToggleNotifications apiModel={MockModelAPI} />
    );
    await sleep(0);
    wrapper.update();

    expect(
      wrapper.find('NotificationList').state('startedTemplateIds')
    ).toEqual([3]);
    const items = wrapper.find('NotificationListItem');
    items
      .at(2)
      .find('Switch')
      .at(0)
      .prop('onChange')();
    expect(MockModelAPI.disassociateNotificationTemplate).toHaveBeenCalledWith(
      1,
      3,
      'started'
    );
    await sleep(0);
    wrapper.update();
    expect(
      wrapper.find('NotificationList').state('startedTemplateIds')
    ).toEqual([]);
  });
});
