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
          <li key={itemId} className="pf-c-data-list__item pf-u-flex-row pf-u-align-items-center">
            <div className="pf-c-data-list__cell pf-u-flex-row">
              <div className="pf-u-display-inline-flex">
                <Link
                  to={{
                    pathname: detailUrl
                  }}
                >
                  <b>{name}</b>
                </Link>
              </div>
              <Badge
                style={capText}
                className="pf-u-display-inline-flex"
                isRead
              >
                {notificationType}
              </Badge>
            </div>
            <div className="pf-c-data-list__cell" />
            <div className="pf-c-data-list__cell pf-u-display-flex pf-u-justify-content-flex-end">
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

