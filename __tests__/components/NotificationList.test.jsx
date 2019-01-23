import React from 'react';
import { mount } from 'enzyme';
import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';
import Notifications from '../../src/components/NotificationsList/Notifications.list';

describe('<Notifications />', () => {
  test('initially renders succesfully', () => {
    mount(
      <MemoryRouter>
        <I18nProvider>
          <Notifications
            match={{ path: '/organizations/:id/?tab=notifications', url: '/organizations/:id/?tab=notifications' }}
            location={{ search: '', pathname: '/organizations/:id/?tab=notifications' }}
          />
        </I18nProvider>
      </MemoryRouter>
    );
  });
  test('fetches notifications on mount', () => {
    const spy = jest.spyOn(Notifications.prototype, 'fetchNotifications');
    mount(
      <MemoryRouter>
        <I18nProvider>
          <Notifications
            match={{ path: '/organizations/:id/?tab=notifications', url: '/organizations/:id/?tab=notifications' }}
            location={{ search: '', pathname: '/organizations/:id/?tab=notifications' }}
          />
        </I18nProvider>
      </MemoryRouter>
    );
    expect(spy).toHaveBeenCalled();
  });
  test('toggle success calls post', () => {
    const spy = jest.spyOn(Notifications.prototype, 'postToSuccess');
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <Notifications
            match={{ path: '/organizations/:id/?tab=notifications', url: '/organizations/:id/?tab=notifications' }}
            location={{ search: '', pathname: '/organizations/:id/?tab=notifications' }}
          />
        </I18nProvider>
      </MemoryRouter>
    ).find('Notifications');
    wrapper.instance().toggleNotification(1, true, 'success');
    expect(spy).toHaveBeenCalledWith(1, true);
  });
  test('post success makes request and updates state properly', async () => {
    const postSuccessFn = jest.fn();
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <Notifications
            match={{ path: '/organizations/:id/?tab=notifications', url: '/organizations/:id/?tab=notifications', params: { id: 1 } }}
            location={{ search: '', pathname: '/organizations/:id/?tab=notifications' }}
            postSuccess={postSuccessFn}
          />
        </I18nProvider>
      </MemoryRouter>
    ).find('Notifications');
    wrapper.setState({ successTemplateIds: [44] });
    await wrapper.instance().postToSuccess(44, true);
    expect(postSuccessFn).toHaveBeenCalledWith(1, { id: 44, disassociate: true });
    expect(wrapper.state('successTemplateIds')).not.toContain(44);
    await wrapper.instance().postToSuccess(44, false);
    expect(postSuccessFn).toHaveBeenCalledWith(1, { id: 44 });
    expect(wrapper.state('successTemplateIds')).toContain(44);
  });
  test('toggle error calls post', () => {
    const spy = jest.spyOn(Notifications.prototype, 'postToError');
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <Notifications
            match={{ path: '/organizations/:id/?tab=notifications', url: '/organizations/:id/?tab=notifications' }}
            location={{ search: '', pathname: '/organizations/:id/?tab=notifications' }}
          />
        </I18nProvider>
      </MemoryRouter>
    ).find('Notifications');
    wrapper.instance().toggleNotification(1, true, 'error');
    expect(spy).toHaveBeenCalledWith(1, true);
  });
  test('post error makes request and updates state properly', async () => {
    const postErrorFn = jest.fn();
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <Notifications
            match={{ path: '/organizations/:id/?tab=notifications', url: '/organizations/:id/?tab=notifications', params: { id: 1 } }}
            location={{ search: '', pathname: '/organizations/:id/?tab=notifications' }}
            postError={postErrorFn}
          />
        </I18nProvider>
      </MemoryRouter>
    ).find('Notifications');
    wrapper.setState({ errorTemplateIds: [44] });
    await wrapper.instance().postToError(44, true);
    expect(postErrorFn).toHaveBeenCalledWith(1, { id: 44, disassociate: true });
    expect(wrapper.state('errorTemplateIds')).not.toContain(44);
    await wrapper.instance().postToError(44, false);
    expect(postErrorFn).toHaveBeenCalledWith(1, { id: 44 });
    expect(wrapper.state('errorTemplateIds')).toContain(44);
  });
  test('fetchNotifications', async () => {
    const mockQueryParams = {
      page: 44,
      page_size: 10,
      order_by: 'name'
    };
    const getNotificationsFn = jest.fn().mockResolvedValue({
      data: {
        results: [
          { id: 1 },
          { id: 2 },
          { id: 3 }
        ]
      }
    });
    const getSuccessFn = jest.fn().mockResolvedValue({
      data: {
        results: [
          { id: 1 }
        ]
      }
    });
    const getErrorFn = jest.fn().mockResolvedValue({
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
            getNotifications={getNotificationsFn}
            getSuccess={getSuccessFn}
            getError={getErrorFn}
          />
        </I18nProvider>
      </MemoryRouter>
    ).find('Notifications');
    wrapper.instance().updateUrl = jest.fn();
    await wrapper.instance().fetchNotifications(mockQueryParams);
    expect(getNotificationsFn).toHaveBeenCalledWith(1, mockQueryParams);
    expect(getSuccessFn).toHaveBeenCalledWith(1, {
      id__in: '1,2,3'
    });
    expect(getErrorFn).toHaveBeenCalledWith(1, {
      id__in: '1,2,3'
    });
    expect(wrapper.state('successTemplateIds')).toContain(1);
    expect(wrapper.state('errorTemplateIds')).toContain(2);
  });
});
