import React from 'react';
import PropTypes from 'prop-types';
import { I18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Link
} from 'react-router-dom';
import {
  Badge,
  Switch
} from '@patternfly/react-core';

class NotificationListItem extends React.Component {
  render () {
    const {
      itemId,
      name,
      notificationType,
      detailUrl,
      successTurnedOn,
      errorTurnedOn,
      toggleNotification
    } = this.props;
    const capText = {
      textTransform: 'capitalize'
    };

    return (
      <I18n>
        {({ i18n }) => (
          <li key={itemId} className="pf-c-data-list__item">
            <div className="pf-c-data-list__cell" style={{ display: 'flex' }}>
              <Link
                to={{
                  pathname: detailUrl
                }}
                style={{ marginRight: '1.5em' }}
              >
                <b>{name}</b>
              </Link>
              <Badge
                style={capText}
                isRead
              >
                {notificationType}
              </Badge>
            </div>
            <div className="pf-c-data-list__cell" style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Switch
                label={i18n._(t`Successful`)}
                isChecked={successTurnedOn}
                onChange={() => toggleNotification(itemId, successTurnedOn, 'success')}
                aria-label={i18n._(t`Notification success toggle`)}
              />
              <Switch
                label={i18n._(t`Failure`)}
                isChecked={errorTurnedOn}
                onChange={() => toggleNotification(itemId, errorTurnedOn, 'error')}
                aria-label={i18n._(t`Notification failure toggle`)}
              />
            </div>
          </li>
        )}
      </I18n>
    );
  }
}

NotificationListItem.propTypes = {
  detailUrl: PropTypes.string.isRequired,
  errorTurnedOn: PropTypes.bool,
  itemId: PropTypes.number.isRequired,
  name: PropTypes.string,
  notificationType: PropTypes.string.isRequired,
  successTurnedOn: PropTypes.bool,
  toggleNotification: PropTypes.func.isRequired,
};

NotificationListItem.defaultProps = {
  errorTurnedOn: false,
  name: null,
  successTurnedOn: false,
};

export default NotificationListItem;
