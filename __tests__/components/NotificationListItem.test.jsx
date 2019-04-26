import React from 'react';
import { mountWithContexts } from '../enzymeHelpers';
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
    wrapper = mountWithContexts(
      <NotificationListItem
        itemId={9000}
        toggleNotification={toggleNotification}
        detailUrl="/foo"
        notificationType="slack"
        canToggleNotifications
      />
    );
    expect(wrapper.length).toBe(1);
  });

  test('handles success click when toggle is on', () => {
    wrapper = mountWithContexts(
      <NotificationListItem
        itemId={9000}
        successTurnedOn
        toggleNotification={toggleNotification}
        detailUrl="/foo"
        notificationType="slack"
        canToggleNotifications
      />
    );
    wrapper.find('Switch').first().find('input').simulate('change');
    expect(toggleNotification).toHaveBeenCalledWith(9000, true, 'success');
  });

  test('handles success click when toggle is off', () => {
    wrapper = mountWithContexts(
      <NotificationListItem
        itemId={9000}
        successTurnedOn={false}
        toggleNotification={toggleNotification}
        detailUrl="/foo"
        notificationType="slack"
        canToggleNotifications
      />
    );
    wrapper.find('Switch').first().find('input').simulate('change');
    expect(toggleNotification).toHaveBeenCalledWith(9000, false, 'success');
  });

  test('handles error click when toggle is on', () => {
    wrapper = mountWithContexts(
      <NotificationListItem
        itemId={9000}
        errorTurnedOn
        toggleNotification={toggleNotification}
        detailUrl="/foo"
        notificationType="slack"
        canToggleNotifications
      />
    );
    wrapper.find('Switch').at(1).find('input').simulate('change');
    expect(toggleNotification).toHaveBeenCalledWith(9000, true, 'error');
  });

  test('handles error click when toggle is off', () => {
    wrapper = mountWithContexts(
      <NotificationListItem
        itemId={9000}
        errorTurnedOn={false}
        toggleNotification={toggleNotification}
        detailUrl="/foo"
        notificationType="slack"
        canToggleNotifications
      />
    );
    wrapper.find('Switch').at(1).find('input').simulate('change');
    expect(toggleNotification).toHaveBeenCalledWith(9000, false, 'error');
  });
});
