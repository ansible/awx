import React, { Component, Fragment } from 'react';
import { number, shape, func, string, bool } from 'prop-types';
import { withRouter } from 'react-router-dom';
import { withNetwork } from '../../../../contexts/Network';
import PaginatedDataList from '../../../../components/PaginatedDataList';
import NotificationListItem from '../../../../components/NotificationsList/NotificationListItem';
import { parseQueryString } from '../../../../util/qs';

const DEFAULT_QUERY_PARAMS = {
  page: 1,
  page_size: 5,
  order_by: 'name',
};

const COLUMNS = [
  { key: 'name', name: 'Name', isSortable: true },
  { key: 'modified', name: 'Modified', isSortable: true, isNumeric: true },
  { key: 'created', name: 'Created', isSortable: true, isNumeric: true },
];

class OrganizationNotifications extends Component {
  constructor (props) {
    super(props);

    this.readNotifications = this.readNotifications.bind(this);
    this.readSuccessesAndErrors = this.readSuccessesAndErrors.bind(this);
    this.toggleNotification = this.toggleNotification.bind(this);

    this.state = {
      isInitialized: false,
      isLoading: false,
      error: null,
      itemCount: 0,
      notifications: [],
      successTemplateIds: [],
      errorTemplateIds: [],
    };
  }

  componentDidMount () {
    this.readNotifications();
  }

  componentDidUpdate (prevProps) {
    const { location } = this.props;
    if (location !== prevProps.location) {
      this.readNotifications();
    }
  }

  getQueryParams () {
    const { location } = this.props;
    const searchParams = parseQueryString(location.search.substring(1));

    return {
      ...DEFAULT_QUERY_PARAMS,
      ...searchParams,
    };
  }

  async readNotifications () {
    const { api, handleHttpError, id } = this.props;
    const params = this.getQueryParams();
    this.setState({ isLoading: true });
    try {
      const { data } = await api.getOrganizationNotifications(id, params);
      this.setState(
        {
          itemCount: data.count || 0,
          notifications: data.results || [],
          isLoading: false,
          isInitialized: true,
        },
        this.readSuccessesAndErrors
      );
    } catch (error) {
      handleHttpError(error) || this.setState({
        error,
        isLoading: false,
      });
    }
  }

  async readSuccessesAndErrors () {
    const { api, handleHttpError, id } = this.props;
    const { notifications } = this.state;
    if (!notifications.length) {
      return;
    }
    const ids = notifications.map(n => n.id).join(',');
    try {
      const successTemplatesPromise = api.getOrganizationNotificationSuccess(
        id,
        { id__in: ids }
      );
      const errorTemplatesPromise = api.getOrganizationNotificationError(
        id,
        { id__in: ids }
      );
      const { data: successTemplates } = await successTemplatesPromise;
      const { data: errorTemplates } = await errorTemplatesPromise;

      this.setState({
        successTemplateIds: successTemplates.results.map(s => s.id),
        errorTemplateIds: errorTemplates.results.map(e => e.id),
      });
    } catch (error) {
      handleHttpError(error) || this.setState({
        error,
        isLoading: false,
      });
    }
  }

  toggleNotification = (notificationId, isCurrentlyOn, status) => {
    if (status === 'success') {
      this.createSuccess(notificationId, isCurrentlyOn);
    } else if (status === 'error') {
      this.createError(notificationId, isCurrentlyOn);
    }
  };

  async createSuccess (notificationId, isCurrentlyOn) {
    const { id, api, handleHttpError } = this.props;
    const postParams = { id: notificationId };
    if (isCurrentlyOn) {
      postParams.disassociate = true;
    }
    try {
      await api.createOrganizationNotificationSuccess(id, postParams);
      if (isCurrentlyOn) {
        this.setState((prevState) => ({
          successTemplateIds: prevState.successTemplateIds
            .filter((templateId) => templateId !== notificationId)
        }));
      } else {
        this.setState(prevState => ({
          successTemplateIds: [...prevState.successTemplateIds, notificationId]
        }));
      }
    } catch (err) {
      handleHttpError(err) || this.setState({ error: true });
    }
  }

  async createError (notificationId, isCurrentlyOn) {
    const { id, api, handleHttpError } = this.props;
    const postParams = { id: notificationId };
    if (isCurrentlyOn) {
      postParams.disassociate = true;
    }
    try {
      await api.createOrganizationNotificationError(id, postParams);
      if (isCurrentlyOn) {
        this.setState((prevState) => ({
          errorTemplateIds: prevState.errorTemplateIds
            .filter((templateId) => templateId !== notificationId)
        }));
      } else {
        this.setState(prevState => ({
          errorTemplateIds: [...prevState.errorTemplateIds, notificationId]
        }));
      }
    } catch (err) {
      handleHttpError(err) || this.setState({ error: true });
    }
  }

  render () {
    const { canToggleNotifications } = this.props;
    const {
      notifications,
      itemCount,
      isLoading,
      isInitialized,
      error,
      successTemplateIds,
      errorTemplateIds,
    } = this.state;

    if (error) {
      // TODO: better error state
      return <div>{error.message}</div>;
    }
    // TODO: better loading state
    return (
      <Fragment>
        {isLoading && (<div>Loading...</div>)}
        {isInitialized && (
          <PaginatedDataList
            items={notifications}
            itemCount={itemCount}
            itemName="notification"
            queryParams={this.getQueryParams()}
            toolbarColumns={COLUMNS}
            renderItem={(notification) => (
              <NotificationListItem
                key={notification.id}
                notification={notification}
                detailUrl={`/notifications/${notification.id}`}
                canToggleNotifications={canToggleNotifications}
                toggleNotification={this.toggleNotification}
                errorTurnedOn={errorTemplateIds.includes(notification.id)}
                successTurnedOn={successTemplateIds.includes(notification.id)}
              />
            )}
          />
        )}
      </Fragment>
    );
  }
}

OrganizationNotifications.propTypes = {
  id: number.isRequired,
  canToggleNotifications: bool.isRequired,
  handleHttpError: func.isRequired,
  api: shape({
    getOrganizationNotifications: func.isRequired,
    getOrganizationNotificationSuccess: func.isRequired,
    getOrganizationNotificationError: func.isRequired,
    createOrganizationNotificationSuccess: func.isRequired,
    createOrganizationNotificationError: func.isRequired,
  }).isRequired,
  location: shape({
    search: string.isRequired,
  }).isRequired,
};

export { OrganizationNotifications as _OrganizationNotifications };
export default withNetwork(withRouter(OrganizationNotifications));
