import React, { Component, Fragment } from 'react';
import { number, shape, string, bool } from 'prop-types';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import AlertModal from '../../../../components/AlertModal';
import PaginatedDataList from '../../../../components/PaginatedDataList';
import NotificationListItem from '../../../../components/NotificationsList/NotificationListItem';
import { getQSConfig, parseNamespacedQueryString } from '../../../../util/qs';
import { OrganizationsAPI } from '../../../../api';

const QS_CONFIG = getQSConfig('notification', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

const COLUMNS = [
  { key: 'name', name: 'Name', isSortable: true },
  { key: 'modified', name: 'Modified', isSortable: true, isNumeric: true },
  { key: 'created', name: 'Created', isSortable: true, isNumeric: true },
];

class OrganizationNotifications extends Component {
  constructor (props) {
    super(props);
    this.state = {
      contentError: false,
      contentLoading: true,
      toggleError: false,
      toggleLoading: false,
      itemCount: 0,
      notifications: [],
      successTemplateIds: [],
      errorTemplateIds: [],
    };
    this.handleNotificationToggle = this.handleNotificationToggle.bind(this);
    this.handleNotificationErrorClose = this.handleNotificationErrorClose.bind(this);
    this.loadNotifications = this.loadNotifications.bind(this);
  }

  componentDidMount () {
    this.loadNotifications();
  }

  componentDidUpdate (prevProps) {
    const { location } = this.props;
    if (location !== prevProps.location) {
      this.loadNotifications();
    }
  }

  async loadNotifications () {
    const { id, location } = this.props;
    const params = parseNamespacedQueryString(QS_CONFIG, location.search);

    this.setState({ contentError: false, contentLoading: true });
    try {
      const {
        data: {
          count: itemCount = 0,
          results: notifications = [],
        }
      } = await OrganizationsAPI.readNotificationTemplates(id, params);

      let idMatchParams;
      if (notifications.length > 0) {
        idMatchParams = { id__in: notifications.map(n => n.id).join(',') };
      } else {
        idMatchParams = {};
      }

      const [
        { data: successTemplates },
        { data: errorTemplates },
      ] = await Promise.all([
        OrganizationsAPI.readNotificationTemplatesSuccess(id, idMatchParams),
        OrganizationsAPI.readNotificationTemplatesError(id, idMatchParams),
      ]);

      this.setState({
        itemCount,
        notifications,
        successTemplateIds: successTemplates.results.map(s => s.id),
        errorTemplateIds: errorTemplates.results.map(e => e.id),
      });
    } catch {
      this.setState({ contentError: true });
    } finally {
      this.setState({ contentLoading: false });
    }
  }

  async handleNotificationToggle (notificationId, isCurrentlyOn, status) {
    const { id } = this.props;

    let stateArrayName;
    if (status === 'success') {
      stateArrayName = 'successTemplateIds';
    } else {
      stateArrayName = 'errorTemplateIds';
    }

    let stateUpdateFunction;
    if (isCurrentlyOn) {
      // when switching off, remove the toggled notification id from the array
      stateUpdateFunction = (prevState) => ({
        [stateArrayName]: prevState[stateArrayName].filter(i => i !== notificationId)
      });
    } else {
      // when switching on, add the toggled notification id to the array
      stateUpdateFunction = (prevState) => ({
        [stateArrayName]: prevState[stateArrayName].concat(notificationId)
      });
    }

    this.setState({ toggleLoading: true });
    try {
      await OrganizationsAPI.updateNotificationTemplateAssociation(
        id,
        notificationId,
        status,
        !isCurrentlyOn
      );
      this.setState(stateUpdateFunction);
    } catch (err) {
      this.setState({ toggleError: true });
    } finally {
      this.setState({ toggleLoading: false });
    }
  }

  handleNotificationErrorClose () {
    this.setState({ toggleError: false });
  }

  render () {
    const { canToggleNotifications, i18n } = this.props;
    const {
      contentError,
      contentLoading,
      toggleError,
      toggleLoading,
      itemCount,
      notifications,
      successTemplateIds,
      errorTemplateIds,
    } = this.state;

    return (
      <Fragment>
        <PaginatedDataList
          contentError={contentError}
          contentLoading={contentLoading}
          items={notifications}
          itemCount={itemCount}
          itemName="notification"
          qsConfig={QS_CONFIG}
          toolbarColumns={COLUMNS}
          renderItem={(notification) => (
            <NotificationListItem
              key={notification.id}
              notification={notification}
              detailUrl={`/notifications/${notification.id}`}
              canToggleNotifications={canToggleNotifications && !toggleLoading}
              toggleNotification={this.handleNotificationToggle}
              errorTurnedOn={errorTemplateIds.includes(notification.id)}
              successTurnedOn={successTemplateIds.includes(notification.id)}
            />
          )}
        />
        <AlertModal
          variant="danger"
          title={i18n._(t`Error!`)}
          isOpen={toggleError && !toggleLoading}
          onClose={this.handleNotificationErrorClose}
        >
          {i18n._(t`Failed to toggle notification.`)}
        </AlertModal>
      </Fragment>
    );
  }
}

OrganizationNotifications.propTypes = {
  id: number.isRequired,
  canToggleNotifications: bool.isRequired,
  location: shape({
    search: string.isRequired,
  }).isRequired,
};

export { OrganizationNotifications as _OrganizationNotifications };
export default withI18n()(withRouter(OrganizationNotifications));
