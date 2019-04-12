import React from 'react';
import { mount } from 'enzyme';
import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';
import Notifications, { _Notifications } from '../../src/components/NotificationsList/Notifications.list';

describe('<Notifications />', () => {
  test('initially renders succesfully', () => {
    mount(
      <MemoryRouter>
        <I18nProvider>
          <Notifications
            match={{ path: '/organizations/:id/?tab=notifications', url: '/organizations/:id/?tab=notifications' }}
            location={{ search: '', pathname: '/organizations/:id/?tab=notifications' }}
            onReadError={jest.fn()}
            onReadNotifications={jest.fn()}
            onReadSuccess={jest.fn()}
            onCreateError={jest.fn()}
            onCreateSuccess={jest.fn()}
            handleHttpError={() => {}}
          />
        </I18nProvider>
      </MemoryRouter>
    );
  });

  test('fetches notifications on mount', () => {
    const spy = jest.spyOn(_Notifications.prototype, 'readNotifications');
    mount(
      <I18nProvider>
        <_Notifications
          match={{ path: '/organizations/:id/?tab=notifications', url: '/organizations/:id/?tab=notifications' }}
          location={{ search: '', pathname: '/organizations/:id/?tab=notifications' }}
          onReadError={jest.fn()}
          onReadNotifications={jest.fn()}
          onReadSuccess={jest.fn()}
          onCreateError={jest.fn()}
          onCreateSuccess={jest.fn()}
          handleHttpError={() => {}}
        />
      </I18nProvider>
    );
    expect(spy).toHaveBeenCalled();
  });

  test('toggle success calls post', () => {
    const spy = jest.spyOn(_Notifications.prototype, 'createSuccess');
    const wrapper = mount(
      <I18nProvider>
        <_Notifications
          match={{ path: '/organizations/:id/?tab=notifications', url: '/organizations/:id/?tab=notifications' }}
          location={{ search: '', pathname: '/organizations/:id/?tab=notifications' }}
          onReadError={jest.fn()}
          onReadNotifications={jest.fn()}
          onReadSuccess={jest.fn()}
          onCreateError={jest.fn()}
          onCreateSuccess={jest.fn()}
          handleHttpError={() => {}}
        />
      </I18nProvider>
    ).find('Notifications');
    wrapper.instance().toggleNotification(1, true, 'success');
    expect(spy).toHaveBeenCalledWith(1, true);
  });

  test('post success makes request and updates state properly', async () => {
    const createSuccess = jest.fn();
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <Notifications
            match={{ path: '/organizations/:id/?tab=notifications', url: '/organizations/:id/?tab=notifications', params: { id: 1 } }}
            location={{ search: '', pathname: '/organizations/:id/?tab=notifications' }}
            onReadError={jest.fn()}
            onReadNotifications={jest.fn()}
            onReadSuccess={jest.fn()}
            onCreateError={jest.fn()}
            onCreateSuccess={createSuccess}
            handleHttpError={() => {}}
          />
        </I18nProvider>
      </MemoryRouter>
    ).find('Notifications');
    wrapper.setState({ successTemplateIds: [44] });
    await wrapper.instance().createSuccess(44, true);
    expect(createSuccess).toHaveBeenCalledWith(1, { id: 44, disassociate: true });
    expect(wrapper.state('successTemplateIds')).not.toContain(44);
    await wrapper.instance().createSuccess(44, false);
    expect(createSuccess).toHaveBeenCalledWith(1, { id: 44 });
    expect(wrapper.state('successTemplateIds')).toContain(44);
  });

  test('toggle error calls post', () => {
    const spy = jest.spyOn(_Notifications.prototype, 'createError');
    const wrapper = mount(
      <I18nProvider>
        <_Notifications
          match={{ path: '/organizations/:id/?tab=notifications', url: '/organizations/:id/?tab=notifications' }}
          location={{ search: '', pathname: '/organizations/:id/?tab=notifications' }}
          onReadError={jest.fn()}
          onReadNotifications={jest.fn()}
          onReadSuccess={jest.fn()}
          onCreateError={jest.fn()}
          onCreateSuccess={jest.fn()}
          handleHttpError={() => {}}
        />
      </I18nProvider>
    ).find('Notifications');
    wrapper.instance().toggleNotification(1, true, 'error');
    expect(spy).toHaveBeenCalledWith(1, true);
  });

  test('post error makes request and updates state properly', async () => {
    const createError = jest.fn();
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <Notifications
            match={{ path: '/organizations/:id/?tab=notifications', url: '/organizations/:id/?tab=notifications', params: { id: 1 } }}
            location={{ search: '', pathname: '/organizations/:id/?tab=notifications' }}
            onReadError={jest.fn()}
            onReadNotifications={jest.fn()}
            onReadSuccess={jest.fn()}
            onCreateError={createError}
            onCreateSuccess={jest.fn()}
            handleHttpError={() => {}}
          />
        </I18nProvider>
      </MemoryRouter>
    ).find('Notifications');
    wrapper.setState({ errorTemplateIds: [44] });
    await wrapper.instance().createError(44, true);
    expect(createError).toHaveBeenCalledWith(1, { id: 44, disassociate: true });
    expect(wrapper.state('errorTemplateIds')).not.toContain(44);
    await wrapper.instance().createError(44, false);
    expect(createError).toHaveBeenCalledWith(1, { id: 44 });
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
    const readError = jest.fn().mockResolvedValue({
      data: {
        results: [
          { id: 2 }
        ]
      }
    });
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <Notifications
            match={{ path: '/organizations/:id/?tab=notifications', url: '/organizations/:id/?tab=notifications', params: { id: 1 } }}
            location={{ search: '', pathname: '/organizations/:id/?tab=notifications' }}
            onReadNotifications={onReadNotifications}
            onReadSuccess={onReadSuccess}
            onReadError={readError}
            onCreateError={jest.fn()}
            onCreateSuccess={jest.fn()}
            handleHttpError={() => {}}
          />
        </I18nProvider>
      </MemoryRouter>
    ).find('Notifications');
    wrapper.instance().updateUrl = jest.fn();
    await wrapper.instance().readNotifications(mockQueryParams);
    expect(onReadNotifications).toHaveBeenCalledWith(1, mockQueryParams);
    expect(onReadSuccess).toHaveBeenCalledWith(1, {
      id__in: '1,2,3'
    });
    expect(readError).toHaveBeenCalledWith(1, {
      id__in: '1,2,3'
    });
    expect(wrapper.state('successTemplateIds')).toContain(1);
    expect(wrapper.state('errorTemplateIds')).toContain(2);
  });
});
