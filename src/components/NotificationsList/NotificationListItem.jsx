import React from 'react';
import { shape, number, string, bool, func } from 'prop-types';
import { I18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import {
  Badge,
  Switch,
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  DataListCell,
} from '@patternfly/react-core';

function NotificationListItem (props) {
  const {
    canToggleNotifications,
    notification,
    detailUrl,
    successTurnedOn,
    errorTurnedOn,
    toggleNotification
  } = props;
  const capText = {
    textTransform: 'capitalize'
  };
  const toggleCellStyles = {
    display: 'flex',
    justifyContent: 'flex-end',
  };

  return (
    <I18n>
      {({ i18n }) => (
        <DataListItem
          aria-labelledby={`items-list-item-${notification.id}`}
          key={notification.id}
        >
          <DataListItemRow>
            <DataListItemCells dataListCells={[
              <DataListCell key="name">
                <Link
                  to={{
                    pathname: detailUrl
                  }}
                  style={{ marginRight: '1.5em' }}
                >
                  <b id={`items-list-item-${notification.id}`}>{notification.name}</b>
                </Link>
                <Badge
                  style={capText}
                  isRead
                >
                  {notification.notification_type}
                </Badge>
              </DataListCell>,
              <DataListCell key="toggles" style={toggleCellStyles}>
                <Switch
                  id={`notification-${notification.id}-success-toggle`}
                  label={i18n._(t`Successful`)}
                  isChecked={successTurnedOn}
                  isDisabled={!canToggleNotifications}
                  onChange={() => toggleNotification(
                    notification.id,
                    successTurnedOn,
                    'success'
                  )}
                  aria-label={i18n._(t`Toggle notification success`)}
                />
                <Switch
                  id={`notification-${notification.id}-error-toggle`}
                  label={i18n._(t`Failure`)}
                  isChecked={errorTurnedOn}
                  isDisabled={!canToggleNotifications}
                  onChange={() => toggleNotification(
                    notification.id,
                    errorTurnedOn,
                    'error'
                  )}
                  aria-label={i18n._(t`Toggle notification failure`)}
                />
              </DataListCell>
            ]}
            />
          </DataListItemRow>
        </DataListItem>
      )}
    </I18n>
  );
}

NotificationListItem.propTypes = {
  notification: shape({
    id: number.isRequired,
    name: string.isRequired,
    notification_type: string.isRequired,
  }).isRequired,
  canToggleNotifications: bool.isRequired,
  detailUrl: string.isRequired,
  errorTurnedOn: bool,
  successTurnedOn: bool,
  toggleNotification: func.isRequired,
};

NotificationListItem.defaultProps = {
  errorTurnedOn: false,
  successTurnedOn: false,
};

export default NotificationListItem;
