import React from 'react';
import { shape, number, string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import {
  DataListAction as _DataListAction,
  DataListItem,
  DataListItemCells,
  DataListItemRow,
  Switch,
} from '@patternfly/react-core';
import DataListCell from '@components/DataListCell';

import styled from 'styled-components';

const DataListAction = styled(_DataListAction)`
  align-items: center;
  display: grid;
  grid-gap: 16px;
  grid-template-columns: repeat(3, max-content);
`;

function NotificationListItem(props) {
  const {
    canToggleNotifications,
    notification,
    detailUrl,
    startedTurnedOn,
    successTurnedOn,
    errorTurnedOn,
    toggleNotification,
    i18n,
    typeLabels,
  } = props;

  return (
    <DataListItem
      aria-labelledby={`items-list-item-${notification.id}`}
      key={notification.id}
      id={`${notification.id}`}
    >
      <DataListItemRow>
        <DataListItemCells
          dataListCells={[
            <DataListCell key="name">
              <Link
                to={{
                  pathname: detailUrl,
                }}
              >
                <b id={`items-list-item-${notification.id}`}>
                  {notification.name}
                </b>
              </Link>
            </DataListCell>,
            <DataListCell key="type">
              {typeLabels[notification.notification_type]}
            </DataListCell>,
          ]}
        />
        <DataListAction
          aria-label="actions"
          aria-labelledby={`items-list-item-${notification.id}`}
          id={`items-list-item-${notification.id}`}
        >
          <Switch
            id={`notification-${notification.id}-started-toggle`}
            label={i18n._(t`Start`)}
            labelOff={i18n._(t`Start`)}
            isChecked={startedTurnedOn}
            isDisabled={!canToggleNotifications}
            onChange={() =>
              toggleNotification(notification.id, startedTurnedOn, 'started')
            }
            aria-label={i18n._(t`Toggle notification start`)}
          />
          <Switch
            id={`notification-${notification.id}-success-toggle`}
            label={i18n._(t`Success`)}
            labelOff={i18n._(t`Success`)}
            isChecked={successTurnedOn}
            isDisabled={!canToggleNotifications}
            onChange={() =>
              toggleNotification(notification.id, successTurnedOn, 'success')
            }
            aria-label={i18n._(t`Toggle notification success`)}
          />
          <Switch
            id={`notification-${notification.id}-error-toggle`}
            label={i18n._(t`Failure`)}
            labelOff={i18n._(t`Failure`)}
            isChecked={errorTurnedOn}
            isDisabled={!canToggleNotifications}
            onChange={() =>
              toggleNotification(notification.id, errorTurnedOn, 'error')
            }
            aria-label={i18n._(t`Toggle notification failure`)}
          />
        </DataListAction>
      </DataListItemRow>
    </DataListItem>
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
  startedTurnedOn: bool,
  successTurnedOn: bool,
  toggleNotification: func.isRequired,
  typeLabels: shape().isRequired,
};

NotificationListItem.defaultProps = {
  errorTurnedOn: false,
  startedTurnedOn: false,
  successTurnedOn: false,
};

export default withI18n()(NotificationListItem);
