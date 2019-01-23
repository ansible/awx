import React, { Fragment } from 'react';
import { I18n } from '@lingui/react';
import { Trans, t } from '@lingui/macro';
import {
  Card,
  CardHeader,
  CardBody,
} from '@patternfly/react-core';
import {
  Switch,
  Link,
  Route
} from 'react-router-dom';

import NotificationsList from '../../../../components/NotificationsList/Notifications.list';

import Tab from '../../../../components/Tabs/Tab';
import Tabs from '../../../../components/Tabs/Tabs';
import getTabName from '../../utils';

const OrganizationDetail = ({
  location,
  match,
  parentBreadcrumbObj,
  organization,
  params,
  currentTab,
  api,
  history
}) => {
  // TODO: set objectName by param or through grabbing org detail get from api
  const tabList = ['details', 'access', 'teams', 'notifications'];

  const deleteResourceView = () => (
    <Fragment>
      <Trans>{`deleting ${currentTab} association with orgs  `}</Trans>
      <Link to={{ pathname: `${match.url}`, search: `?${params.toString()}`, state: { breadcrumb: parentBreadcrumbObj, organization } }}>
        <Trans>{`confirm removal of ${currentTab}/cancel and go back to ${currentTab} view.`}</Trans>
      </Link>
    </Fragment>
  );

  const addResourceView = () => (
    <Fragment>
      <Trans>{`adding ${currentTab}   `}</Trans>
      <Link to={{ pathname: `${match.url}`, search: `?${params.toString()}`, state: { breadcrumb: parentBreadcrumbObj, organization } }}>
        <Trans>{`save/cancel and go back to ${currentTab} view`}</Trans>
      </Link>
    </Fragment>
  );

  const resourceView = () => {
    let relatedTemplate;
    switch (currentTab) {
      case 'notifications':
        relatedTemplate = (
          <NotificationsList
            getNotifications={(id, reqParams) => api.getOrganizationNotifications(id, reqParams)}
            getSuccess={(id, reqParams) => api.getOrganizationNotificationSuccess(id, reqParams)}
            getError={(id, reqParams) => api.getOrganizationNotificationError(id, reqParams)}
            postSuccess={(id, data) => api.createOrganizationNotificationSuccess(id, data)}
            postError={(id, data) => api.createOrganizationNotificationError(id, data)}
            match={match}
            location={location}
            history={history}
          />
        );
        break;
      default:
        relatedTemplate = (
          <Fragment>
            <Trans>{`${currentTab} detail view  `}</Trans>
            <Link to={{ pathname: `${match.url}/add-resource`, search: `?${params.toString()}`, state: { breadcrumb: parentBreadcrumbObj, organization } }}>
              <Trans>{`add ${currentTab}`}</Trans>
            </Link>
            {'  '}
            <Link to={{ pathname: `${match.url}/delete-resources`, search: `?${params.toString()}`, state: { breadcrumb: parentBreadcrumbObj, organization } }}>
              <Trans>{`delete ${currentTab}`}</Trans>
            </Link>
          </Fragment>
        );
    }
    return relatedTemplate;
  };

  return (
    <Card className="at-c-orgPane">
      <CardHeader>
        <I18n>
          {({ i18n }) => (
            <Tabs labelText={i18n._(t`Organization detail tabs`)}>
              {tabList.map(tab => (
                <Tab
                  key={tab}
                  tab={tab}
                  location={location}
                  match={match}
                  currentTab={currentTab}
                  breadcrumb={parentBreadcrumbObj}
                >
                  <Trans>{getTabName(tab)}</Trans>
                </Tab>
              ))}
            </Tabs>
          )}
        </I18n>
      </CardHeader>
      <CardBody className="at-c-listCardBody">
        <Switch>
          <Route path={`${match.path}/delete-resources`} component={() => deleteResourceView()} />
          <Route path={`${match.path}/add-resource`} component={() => addResourceView()} />
          <Route path={`${match.path}`} render={(props) => resourceView(props)} />
        </Switch>
      </CardBody>
    </Card>
  );
};

export default OrganizationDetail;
