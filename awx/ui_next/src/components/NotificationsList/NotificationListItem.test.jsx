import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import NotificationListItem from './NotificationListItem';

describe('<NotificationListItem canToggleNotifications />', () => {
  let wrapper;
  let toggleNotification;

  const mockNotif = {
    id: 9000,
    name: 'Foo',
    notification_type: 'slack',
  };

  const typeLabels = {
    slack: 'Slack',
  };

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

  test('initially renders succesfully and displays correct label', () => {
    wrapper = mountWithContexts(
      <NotificationListItem
        notification={mockNotif}
        toggleNotification={toggleNotification}
        detailUrl="/foo"
        canToggleNotifications
        typeLabels={typeLabels}
      />
    );
    expect(wrapper.find('NotificationListItem')).toMatchSnapshot();
  });

  test('displays correct label in correct column', () => {
    wrapper = mountWithContexts(
      <NotificationListItem
        notification={mockNotif}
        toggleNotification={toggleNotification}
        detailUrl="/foo"
        canToggleNotifications
        typeLabels={typeLabels}
      />
    );
    const typeCell = wrapper
      .find('DataListCell')
      .at(1)
      .find('div');
    expect(typeCell.text()).toBe('Slack');
  });

  test('handles start click when toggle is on', () => {
    wrapper = mountWithContexts(
      <NotificationListItem
        notification={mockNotif}
        startedTurnedOn
        toggleNotification={toggleNotification}
        detailUrl="/foo"
        canToggleNotifications
        typeLabels={typeLabels}
      />
    );
    wrapper
      .find('Switch')
      .first()
      .find('input')
      .simulate('change');
    expect(toggleNotification).toHaveBeenCalledWith(9000, true, 'started');
  });

  test('handles start click when toggle is off', () => {
    wrapper = mountWithContexts(
      <NotificationListItem
        notification={mockNotif}
        startedTurnedOn={false}
        toggleNotification={toggleNotification}
        detailUrl="/foo"
        canToggleNotifications
        typeLabels={typeLabels}
      />
    );
    wrapper
      .find('Switch')
      .first()
      .find('input')
      .simulate('change');
    expect(toggleNotification).toHaveBeenCalledWith(9000, false, 'started');
  });

  test('handles error click when toggle is on', () => {
    wrapper = mountWithContexts(
      <NotificationListItem
        notification={mockNotif}
        successTurnedOn
        toggleNotification={toggleNotification}
        detailUrl="/foo"
        canToggleNotifications
        typeLabels={typeLabels}
      />
    );
    wrapper
      .find('Switch')
      .at(1)
      .find('input')
      .simulate('change');
    expect(toggleNotification).toHaveBeenCalledWith(9000, true, 'success');
  });

  test('handles error click when toggle is off', () => {
    wrapper = mountWithContexts(
      <NotificationListItem
        notification={mockNotif}
        successTurnedOn={false}
        toggleNotification={toggleNotification}
        detailUrl="/foo"
        canToggleNotifications
        typeLabels={typeLabels}
      />
    );
    wrapper
      .find('Switch')
      .at(1)
      .find('input')
      .simulate('change');
    expect(toggleNotification).toHaveBeenCalledWith(9000, false, 'success');
  });

  test('handles error click when toggle is on', () => {
    wrapper = mountWithContexts(
      <NotificationListItem
        notification={mockNotif}
        errorTurnedOn
        toggleNotification={toggleNotification}
        detailUrl="/foo"
        canToggleNotifications
        typeLabels={typeLabels}
      />
    );
    wrapper
      .find('Switch')
      .at(2)
      .find('input')
      .simulate('change');
    expect(toggleNotification).toHaveBeenCalledWith(9000, true, 'error');
  });

  test('handles error click when toggle is off', () => {
    wrapper = mountWithContexts(
      <NotificationListItem
        notification={mockNotif}
        errorTurnedOn={false}
        toggleNotification={toggleNotification}
        detailUrl="/foo"
        canToggleNotifications
        typeLabels={typeLabels}
      />
    );
    wrapper
      .find('Switch')
      .at(2)
      .find('input')
      .simulate('change');
    expect(toggleNotification).toHaveBeenCalledWith(9000, false, 'error');
  });
});
