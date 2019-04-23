import React from 'react';
import { mountWithContexts } from '../enzymeHelpers';
import Notifications, { _Notifications } from '../../src/components/NotificationsList/Notifications.list';

describe('<Notifications />', () => {
  test('initially renders succesfully', () => {
    mountWithContexts(
      <Notifications
        onReadError={() => {}}
        onReadNotifications={() => {}}
        onReadSuccess={() => {}}
        onCreateError={() => {}}
        onCreateSuccess={() => {}}
      />
    );
  });

  test('fetches notifications on mount', () => {
    const spy = jest.spyOn(_Notifications.prototype, 'readNotifications');
    mountWithContexts(
      <Notifications
        onReadError={() => {}}
        onReadNotifications={() => {}}
        onReadSuccess={() => {}}
        onCreateError={() => {}}
        onCreateSuccess={() => {}}
      />
    );
    expect(spy).toHaveBeenCalled();
  });

  test('toggle success calls post', () => {
    const spy = jest.spyOn(_Notifications.prototype, 'createSuccess');
    const wrapper = mountWithContexts(
      <Notifications
        onReadError={() => {}}
        onReadNotifications={() => {}}
        onReadSuccess={() => {}}
        onCreateError={() => {}}
        onCreateSuccess={() => {}}
      />
    ).find('Notifications');
    wrapper.instance().toggleNotification(1, true, 'success');
    expect(spy).toHaveBeenCalledWith(1, true);
  });

  test('post success makes request and updates state properly', async () => {
    const onCreateSuccess = jest.fn();
    const wrapper = mountWithContexts(
      <_Notifications
        match={{ path: '/organizations/:id/?tab=notifications', url: '/organizations/:id/?tab=notifications', params: { id: 1 } }}
        location={{ search: '', pathname: '/organizations/:id/?tab=notifications' }}
        handleHttpError={() => {}}
        onReadError={() => {}}
        onReadNotifications={() => {}}
        onReadSuccess={() => {}}
        onCreateError={() => {}}
        onCreateSuccess={onCreateSuccess}
      />
    ).find('Notifications');
    wrapper.setState({ successTemplateIds: [44] });
    await wrapper.instance().createSuccess(44, true);
    expect(onCreateSuccess).toHaveBeenCalledWith(1, { id: 44, disassociate: true });
    expect(wrapper.state('successTemplateIds')).not.toContain(44);
    await wrapper.instance().createSuccess(44, false);
    expect(onCreateSuccess).toHaveBeenCalledWith(1, { id: 44 });
    expect(wrapper.state('successTemplateIds')).toContain(44);
  });

  test('toggle error calls post', () => {
    const spy = jest.spyOn(_Notifications.prototype, 'createError');
    const wrapper = mountWithContexts(
      <Notifications
        onReadError={() => {}}
        onReadNotifications={() => {}}
        onReadSuccess={() => {}}
        onCreateError={() => {}}
        onCreateSuccess={() => {}}
      />
    ).find('Notifications');
    wrapper.instance().toggleNotification(1, true, 'error');
    expect(spy).toHaveBeenCalledWith(1, true);
  });

  test('post error makes request and updates state properly', async () => {
    const onCreateError = jest.fn();
    const wrapper = mountWithContexts(
      <_Notifications
        match={{ path: '/organizations/:id/?tab=notifications', url: '/organizations/:id/?tab=notifications', params: { id: 1 } }}
        location={{ search: '', pathname: '/organizations/:id/?tab=notifications' }}
        handleHttpError={() => {}}
        onReadError={() => {}}
        onReadNotifications={() => {}}
        onReadSuccess={() => {}}
        onCreateError={onCreateError}
        onCreateSuccess={() => {}}
      />
    ).find('Notifications');
    wrapper.setState({ errorTemplateIds: [44] });
    await wrapper.instance().createError(44, true);
    expect(onCreateError).toHaveBeenCalledWith(1, { id: 44, disassociate: true });
    expect(wrapper.state('errorTemplateIds')).not.toContain(44);
    await wrapper.instance().createError(44, false);
    expect(onCreateError).toHaveBeenCalledWith(1, { id: 44 });
    expect(wrapper.state('errorTemplateIds')).toContain(44);
  });

  test('fetchNotifications', async () => {
    const mockQueryParams = {
      page: 44,
      page_size: 10,
      order_by: 'name'
    };
    const onReadNotifications = jest.fn().mockResolvedValue({
      data: {
        results: [
          { id: 1, notification_type: 'slack' },
          { id: 2, notification_type: 'email' },
          { id: 3, notification_type: 'github' }
        ]
      }
    });
    const onReadSuccess = jest.fn().mockResolvedValue({
      data: {
        results: [
          { id: 1 }
        ]
      }
    });
    const onReadError = jest.fn().mockResolvedValue({
      data: {
        results: [
          { id: 2 }
        ]
      }
    });
    const wrapper = mountWithContexts(
      <_Notifications
        match={{ path: '/organizations/:id/?tab=notifications', url: '/organizations/:id/?tab=notifications', params: { id: 1 } }}
        location={{ search: '', pathname: '/organizations/:id/?tab=notifications' }}
        handleHttpError={() => {}}
        onReadError={onReadError}
        onReadNotifications={onReadNotifications}
        onReadSuccess={onReadSuccess}
        onCreateError={() => {}}
        onCreateSuccess={() => {}}
      />
    ).find('Notifications');
    wrapper.instance().updateUrl = jest.fn();
    await wrapper.instance().readNotifications(mockQueryParams);
    expect(onReadNotifications).toHaveBeenCalledWith(1, mockQueryParams);
    expect(onReadSuccess).toHaveBeenCalledWith(1, {
      id__in: '1,2,3'
    });
    expect(onReadError).toHaveBeenCalledWith(1, {
      id__in: '1,2,3'
    });
    expect(wrapper.state('successTemplateIds')).toContain(1);
    expect(wrapper.state('errorTemplateIds')).toContain(2);
  });
});
