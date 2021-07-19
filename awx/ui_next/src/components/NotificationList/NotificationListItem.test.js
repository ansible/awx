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
    jest.clearAllMocks();
  });

  test('initially renders successfully and displays correct label', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <NotificationListItem
            notification={mockNotif}
            toggleNotification={toggleNotification}
            detailUrl="/foo"
            canToggleNotifications
            typeLabels={typeLabels}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('Switch').length).toBe(3);
  });

  test('shows approvals toggle when configured', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <NotificationListItem
            notification={mockNotif}
            toggleNotification={toggleNotification}
            detailUrl="/foo"
            canToggleNotifications
            typeLabels={typeLabels}
            showApprovalsToggle
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('Switch').length).toBe(4);
  });

  test('displays correct type', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <NotificationListItem
            notification={mockNotif}
            toggleNotification={toggleNotification}
            detailUrl="/foo"
            canToggleNotifications
            typeLabels={typeLabels}
          />
        </tbody>
      </table>
    );
    const typeCell = wrapper.find('Td').at(1);
    expect(typeCell.text()).toContain('Slack');
  });

  test('handles approvals click when toggle is on', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <NotificationListItem
            notification={mockNotif}
            approvalsTurnedOn
            toggleNotification={toggleNotification}
            detailUrl="/foo"
            canToggleNotifications
            typeLabels={typeLabels}
            showApprovalsToggle
          />
        </tbody>
      </table>
    );
    wrapper
      .find('Switch[aria-label="Toggle notification approvals"]')
      .first()
      .find('input')
      .simulate('change');
    expect(toggleNotification).toHaveBeenCalledWith(9000, true, 'approvals');
  });

  test('handles approvals click when toggle is off', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <NotificationListItem
            notification={mockNotif}
            approvalsTurnedOn={false}
            toggleNotification={toggleNotification}
            detailUrl="/foo"
            canToggleNotifications
            typeLabels={typeLabels}
            showApprovalsToggle
          />
        </tbody>
      </table>
    );
    wrapper
      .find('Switch[aria-label="Toggle notification approvals"]')
      .find('input')
      .simulate('change');
    expect(toggleNotification).toHaveBeenCalledWith(9000, false, 'approvals');
  });

  test('handles started click when toggle is on', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <NotificationListItem
            notification={mockNotif}
            startedTurnedOn
            toggleNotification={toggleNotification}
            detailUrl="/foo"
            canToggleNotifications
            typeLabels={typeLabels}
          />
        </tbody>
      </table>
    );
    wrapper
      .find('Switch[aria-label="Toggle notification start"]')
      .find('input')
      .simulate('change');
    expect(toggleNotification).toHaveBeenCalledWith(9000, true, 'started');
  });

  test('handles started click when toggle is off', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <NotificationListItem
            notification={mockNotif}
            startedTurnedOn={false}
            toggleNotification={toggleNotification}
            detailUrl="/foo"
            canToggleNotifications
            typeLabels={typeLabels}
          />
        </tbody>
      </table>
    );
    wrapper
      .find('Switch[aria-label="Toggle notification start"]')
      .find('input')
      .simulate('change');
    expect(toggleNotification).toHaveBeenCalledWith(9000, false, 'started');
  });

  test('handles success click when toggle is on', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <NotificationListItem
            notification={mockNotif}
            successTurnedOn
            toggleNotification={toggleNotification}
            detailUrl="/foo"
            canToggleNotifications
            typeLabels={typeLabels}
          />
        </tbody>
      </table>
    );
    wrapper
      .find('Switch[aria-label="Toggle notification success"]')
      .find('input')
      .simulate('change');
    expect(toggleNotification).toHaveBeenCalledWith(9000, true, 'success');
  });

  test('handles success click when toggle is off', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <NotificationListItem
            notification={mockNotif}
            successTurnedOn={false}
            toggleNotification={toggleNotification}
            detailUrl="/foo"
            canToggleNotifications
            typeLabels={typeLabels}
          />
        </tbody>
      </table>
    );
    wrapper
      .find('Switch[aria-label="Toggle notification success"]')
      .find('input')
      .simulate('change');
    expect(toggleNotification).toHaveBeenCalledWith(9000, false, 'success');
  });

  test('handles error click when toggle is on', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <NotificationListItem
            notification={mockNotif}
            errorTurnedOn
            toggleNotification={toggleNotification}
            detailUrl="/foo"
            canToggleNotifications
            typeLabels={typeLabels}
          />
        </tbody>
      </table>
    );
    wrapper
      .find('Switch[aria-label="Toggle notification failure"]')
      .find('input')
      .simulate('change');
    expect(toggleNotification).toHaveBeenCalledWith(9000, true, 'error');
  });

  test('handles error click when toggle is off', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <NotificationListItem
            notification={mockNotif}
            errorTurnedOn={false}
            toggleNotification={toggleNotification}
            detailUrl="/foo"
            canToggleNotifications
            typeLabels={typeLabels}
          />
        </tbody>
      </table>
    );
    wrapper
      .find('Switch[aria-label="Toggle notification failure"]')
      .find('input')
      .simulate('change');
    expect(toggleNotification).toHaveBeenCalledWith(9000, false, 'error');
  });
});
