import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import NotificationListItem from './NotificationListItem';

describe('<NotificationListItem canToggleNotifications />', () => {
  let wrapper;
  let toggleNotification;

  beforeEach(() => {
    toggleNotification = jest.fn();
  });

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount();
      wrapper = null;
    }
    jest.clearAllMocks();
  });

  test('initially renders succesfully', () => {
    wrapper = mountWithContexts(
      <NotificationListItem
        notification={{
          id: 9000,
          name: 'Foo',
          notification_type: 'slack',
        }}
        toggleNotification={toggleNotification}
        detailUrl="/foo"
        canToggleNotifications
      />
    );
    expect(wrapper.find('NotificationListItem')).toMatchSnapshot();
  });

  test('handles success click when toggle is on', () => {
    wrapper = mountWithContexts(
      <NotificationListItem
        notification={{
          id: 9000,
          name: 'Foo',
          notification_type: 'slack',
        }}
        successTurnedOn
        toggleNotification={toggleNotification}
        detailUrl="/foo"
        canToggleNotifications
      />
    );
    wrapper
      .find('Switch')
      .first()
      .find('input')
      .simulate('change');
    expect(toggleNotification).toHaveBeenCalledWith(9000, true, 'success');
  });

  test('handles success click when toggle is off', () => {
    wrapper = mountWithContexts(
      <NotificationListItem
        notification={{
          id: 9000,
          name: 'Foo',
          notification_type: 'slack',
        }}
        successTurnedOn={false}
        toggleNotification={toggleNotification}
        detailUrl="/foo"
        canToggleNotifications
      />
    );
    wrapper
      .find('Switch')
      .first()
      .find('input')
      .simulate('change');
    expect(toggleNotification).toHaveBeenCalledWith(9000, false, 'success');
  });

  test('handles error click when toggle is on', () => {
    wrapper = mountWithContexts(
      <NotificationListItem
        notification={{
          id: 9000,
          name: 'Foo',
          notification_type: 'slack',
        }}
        errorTurnedOn
        toggleNotification={toggleNotification}
        detailUrl="/foo"
        canToggleNotifications
      />
    );
    wrapper
      .find('Switch')
      .at(1)
      .find('input')
      .simulate('change');
    expect(toggleNotification).toHaveBeenCalledWith(9000, true, 'error');
  });

  test('handles error click when toggle is off', () => {
    wrapper = mountWithContexts(
      <NotificationListItem
        notification={{
          id: 9000,
          name: 'Foo',
          notification_type: 'slack',
        }}
        errorTurnedOn={false}
        toggleNotification={toggleNotification}
        detailUrl="/foo"
        canToggleNotifications
      />
    );
    wrapper
      .find('Switch')
      .at(1)
      .find('input')
      .simulate('change');
    expect(toggleNotification).toHaveBeenCalledWith(9000, false, 'error');
  });
});
