import React from 'react';
import { act } from 'react-dom/test-utils';
import { NotificationTemplatesAPI, JobTemplatesAPI } from 'api';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import NotificationList from './NotificationList';

jest.mock('../../api');

describe('<NotificationList />', () => {
  let wrapper;
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

  beforeEach(async () => {
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

    NotificationTemplatesAPI.read.mockReturnValue({ data });

    JobTemplatesAPI.readNotificationTemplatesSuccess.mockReturnValue({
      data: { results: [{ id: 1 }] },
    });

    JobTemplatesAPI.readNotificationTemplatesError.mockReturnValue({
      data: { results: [{ id: 2 }] },
    });

    JobTemplatesAPI.readNotificationTemplatesStarted.mockReturnValue({
      data: { results: [{ id: 3 }] },
    });

    await act(async () => {
      wrapper = mountWithContexts(
        <NotificationList
          id={1}
          canToggleNotifications
          apiModel={JobTemplatesAPI}
        />
      );
    });
    wrapper.update();
  });

  test('should render list fetched of items', () => {
    expect(NotificationTemplatesAPI.read).toHaveBeenCalled();
    expect(NotificationTemplatesAPI.readOptions).toHaveBeenCalled();
    expect(JobTemplatesAPI.readNotificationTemplatesSuccess).toHaveBeenCalled();
    expect(JobTemplatesAPI.readNotificationTemplatesError).toHaveBeenCalled();
    expect(JobTemplatesAPI.readNotificationTemplatesStarted).toHaveBeenCalled();
    expect(wrapper.find('NotificationListItem').length).toBe(3);
    expect(
      wrapper.find('input#notification-1-success-toggle').props().checked
    ).toBe(true);
    expect(
      wrapper.find('input#notification-1-error-toggle').props().checked
    ).toBe(false);
    expect(
      wrapper.find('input#notification-1-started-toggle').props().checked
    ).toBe(false);
    expect(
      wrapper.find('input#notification-2-success-toggle').props().checked
    ).toBe(false);
    expect(
      wrapper.find('input#notification-2-error-toggle').props().checked
    ).toBe(true);
    expect(
      wrapper.find('input#notification-2-started-toggle').props().checked
    ).toBe(false);
    expect(
      wrapper.find('input#notification-3-success-toggle').props().checked
    ).toBe(false);
    expect(
      wrapper.find('input#notification-3-error-toggle').props().checked
    ).toBe(false);
    expect(
      wrapper.find('input#notification-3-started-toggle').props().checked
    ).toBe(true);
  });

  test('should enable success notification', async () => {
    expect(
      wrapper.find('input#notification-2-success-toggle').props().checked
    ).toBe(false);
    await act(async () => {
      wrapper.find('Switch#notification-2-success-toggle').prop('onChange')();
    });
    wrapper.update();
    expect(JobTemplatesAPI.associateNotificationTemplate).toHaveBeenCalledWith(
      1,
      2,
      'success'
    );
    expect(
      wrapper.find('input#notification-2-success-toggle').props().checked
    ).toBe(true);
  });

  test('should enable error notification', async () => {
    expect(
      wrapper.find('input#notification-1-error-toggle').props().checked
    ).toBe(false);
    await act(async () => {
      wrapper.find('Switch#notification-1-error-toggle').prop('onChange')();
    });
    wrapper.update();
    expect(JobTemplatesAPI.associateNotificationTemplate).toHaveBeenCalledWith(
      1,
      1,
      'error'
    );
    expect(
      wrapper.find('input#notification-1-error-toggle').props().checked
    ).toBe(true);
  });

  test('should enable start notification', async () => {
    expect(
      wrapper.find('input#notification-1-started-toggle').props().checked
    ).toBe(false);
    await act(async () => {
      wrapper.find('Switch#notification-1-started-toggle').prop('onChange')();
    });
    wrapper.update();
    expect(JobTemplatesAPI.associateNotificationTemplate).toHaveBeenCalledWith(
      1,
      1,
      'started'
    );
    expect(
      wrapper.find('input#notification-1-started-toggle').props().checked
    ).toBe(true);
  });

  test('should disable success notification', async () => {
    expect(
      wrapper.find('input#notification-1-success-toggle').props().checked
    ).toBe(true);
    await act(async () => {
      wrapper.find('Switch#notification-1-success-toggle').prop('onChange')();
    });
    wrapper.update();
    expect(
      JobTemplatesAPI.disassociateNotificationTemplate
    ).toHaveBeenCalledWith(1, 1, 'success');
    expect(
      wrapper.find('input#notification-1-success-toggle').props().checked
    ).toBe(false);
  });

  test('should disable error notification', async () => {
    expect(
      wrapper.find('input#notification-2-error-toggle').props().checked
    ).toBe(true);
    await act(async () => {
      wrapper.find('Switch#notification-2-error-toggle').prop('onChange')();
    });
    wrapper.update();
    expect(
      JobTemplatesAPI.disassociateNotificationTemplate
    ).toHaveBeenCalledWith(1, 2, 'error');
    expect(
      wrapper.find('input#notification-2-error-toggle').props().checked
    ).toBe(false);
  });

  test('should disable start notification', async () => {
    expect(
      wrapper.find('input#notification-3-started-toggle').props().checked
    ).toBe(true);
    await act(async () => {
      wrapper.find('Switch#notification-3-started-toggle').prop('onChange')();
    });
    wrapper.update();
    expect(
      JobTemplatesAPI.disassociateNotificationTemplate
    ).toHaveBeenCalledWith(1, 3, 'started');
    expect(
      wrapper.find('input#notification-3-started-toggle').props().checked
    ).toBe(false);
  });

  test('should throw toggle error', async () => {
    JobTemplatesAPI.associateNotificationTemplate.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'post',
          },
          data: 'An error occurred',
          status: 403,
        },
      })
    );
    expect(wrapper.find('ErrorDetail').length).toBe(0);
    await act(async () => {
      wrapper.find('Switch#notification-1-started-toggle').prop('onChange')();
    });
    wrapper.update();
    expect(JobTemplatesAPI.associateNotificationTemplate).toHaveBeenCalledWith(
      1,
      1,
      'started'
    );
    expect(wrapper.find('ErrorDetail').length).toBe(1);
  });
});
