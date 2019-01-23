import React from 'react';
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
  constructor (props) {
    super(props);
    this.errorToggleClick = this.errorToggleClick.bind(this);
    this.successToggleClick = this.successToggleClick.bind(this);
  }

  errorToggleClick (flag) {
    const { itemId, toggleError } = this.props;
    toggleError(itemId, flag);
  }

  successToggleClick (flag) {
    const { itemId, toggleSuccess } = this.props;
    toggleSuccess(itemId, flag);
  }

  render () {
    const {
      itemId,
      name,
      notificationType,
      detailUrl,
      parentBreadcrumb,
      successTurnedOn,
      errorTurnedOn
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
                    pathname: detailUrl,
                    state: { breadcrumb: [parentBreadcrumb, { name, url: detailUrl }] }
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
                onChange={() => this.successToggleClick(successTurnedOn)}
                aria-label={i18n._(t`Notification success toggle`)}
              />
              <Switch
                label={i18n._(t`Failure`)}
                isChecked={errorTurnedOn}
                onChange={() => this.errorToggleClick(errorTurnedOn)}
                aria-label={i18n._(t`Notification failure toggle`)}
              />
            </div>
          </li>
        )}
      </I18n>
    );
  }
}

export default NotificationListItem;

