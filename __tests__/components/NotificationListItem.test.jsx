import React from 'react';
import { mount } from 'enzyme';
import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';
import NotificationListItem from '../../src/components/NotificationsList/NotificationListItem';

describe('<NotificationListItem />', () => {
  let wrapper;
  const toggleNotification = jest.fn();

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount();
      wrapper = null;
    }
  });

  test('initially renders succesfully', () => {
    wrapper = mount(
      <I18nProvider>
        <MemoryRouter>
          <NotificationListItem
            itemId={9000}
            toggleNotification={toggleNotification}
            detailUrl="/foo"
            notificationType="slack"
          />
        </MemoryRouter>
      </I18nProvider>
    );
    expect(wrapper.length).toBe(1);
  });

  test('handles success click when toggle is on', () => {
    wrapper = mount(
      <I18nProvider>
        <MemoryRouter>
          <NotificationListItem
            itemId={9000}
            successTurnedOn
            toggleNotification={toggleNotification}
            detailUrl="/foo"
            notificationType="slack"
          />
        </MemoryRouter>
      </I18nProvider>
    );
    wrapper.find('Switch').first().find('input').simulate('change');
    expect(toggleNotification).toHaveBeenCalledWith(9000, true, 'success');
  });

  test('handles success click when toggle is off', () => {
    wrapper = mount(
      <I18nProvider>
        <MemoryRouter>
          <NotificationListItem
            itemId={9000}
            successTurnedOn={false}
            toggleNotification={toggleNotification}
            detailUrl="/foo"
            notificationType="slack"
          />
        </MemoryRouter>
      </I18nProvider>
    );
    wrapper.find('Switch').first().find('input').simulate('change');
    expect(toggleNotification).toHaveBeenCalledWith(9000, false, 'success');
  });

  test('handles error click when toggle is on', () => {
    wrapper = mount(
      <I18nProvider>
        <MemoryRouter>
          <NotificationListItem
            itemId={9000}
            errorTurnedOn
            toggleNotification={toggleNotification}
            detailUrl="/foo"
            notificationType="slack"
          />
        </MemoryRouter>
      </I18nProvider>
    );
    wrapper.find('Switch').at(1).find('input').simulate('change');
    expect(toggleNotification).toHaveBeenCalledWith(9000, true, 'error');
  });

  test('handles error click when toggle is off', () => {
    wrapper = mount(
      <I18nProvider>
        <MemoryRouter>
          <NotificationListItem
            itemId={9000}
            errorTurnedOn={false}
            toggleNotification={toggleNotification}
            detailUrl="/foo"
            notificationType="slack"
          />
        </MemoryRouter>
      </I18nProvider>
    );
    wrapper.find('Switch').at(1).find('input').simulate('change');
    expect(toggleNotification).toHaveBeenCalledWith(9000, false, 'error');
  });
});
