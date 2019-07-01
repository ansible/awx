import React from 'react';
import { shape, number, string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import {
  Switch as PFSwitch,
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  DataListCell as PFDataListCell,
} from '@patternfly/react-core';

import styled from 'styled-components';

const DataListCell = styled(PFDataListCell)`
  display: flex;
  justify-content: ${props => (props.righthalf ? 'flex-start' : 'inherit')};
  padding-bottom: ${props => (props.righthalf ? '16px' : '8px')};

  @media screen and (min-width: 768px) {
    justify-content: ${props => (props.righthalf ? 'flex-end' : 'inherit')};
    padding-bottom: 0;
  }
`;

const Switch = styled(PFSwitch)`
  display: flex;
  flex-wrap: no-wrap;
`;

function NotificationListItem(props) {
  const {
    canToggleNotifications,
    notification,
    detailUrl,
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
    >
      <DataListItemRow>
        <DataListItemCells
          dataListCells={[
            <DataListCell key="name">
              <Link
                to={{
                  pathname: detailUrl,
                }}
                css="margin-right: 1.5em;"
              >
                <b id={`items-list-item-${notification.id}`}>
                  {notification.name}
                </b>
              </Link>
            </DataListCell>,
            <DataListCell key="type">
              {typeLabels[notification.notification_type]}
            </DataListCell>,
            <DataListCell righthalf="true" key="toggles">
              <Switch
                id={`notification-${notification.id}-success-toggle`}
                label={i18n._(t`Successful`)}
                isChecked={successTurnedOn}
                isDisabled={!canToggleNotifications}
                onChange={() =>
                  toggleNotification(
                    notification.id,
                    successTurnedOn,
                    'success'
                  )
                }
                aria-label={i18n._(t`Toggle notification success`)}
              />
              <Switch
                id={`notification-${notification.id}-error-toggle`}
                label={i18n._(t`Failure`)}
                isChecked={errorTurnedOn}
                isDisabled={!canToggleNotifications}
                onChange={() =>
                  toggleNotification(notification.id, errorTurnedOn, 'error')
                }
                aria-label={i18n._(t`Toggle notification failure`)}
              />
            </DataListCell>,
          ]}
        />
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
  successTurnedOn: bool,
  toggleNotification: func.isRequired,
  typeLabels: shape().isRequired,
};

NotificationListItem.defaultProps = {
  errorTurnedOn: false,
  successTurnedOn: false,
};

export default withI18n()(NotificationListItem);
