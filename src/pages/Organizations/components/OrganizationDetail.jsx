import React, { Fragment } from 'react';
import {
  Card,
  CardHeader,
  CardBody,
  PageSection,
  PageSectionVariants,
  ToolbarGroup,
  ToolbarItem,
  ToolbarSection,
} from '@patternfly/react-core';
import {
  Switch,
  Link,
  Route
} from 'react-router-dom';

import getTabName from '../utils';

import '../tabs.scss';

const DetailTab = ({ location, match, tab, currentTab, children, breadcrumb }) => {
  const tabClasses = () => {
    let classes = 'at-c-tabs__tab';
    if (tab === currentTab) {
      classes += ' at-m-selected';
    }

    return classes;
  };

  const updateTab = () => {
    const params = new URLSearchParams(location.search);
    if (params.get('tab') !== undefined) {
      params.set('tab', tab);
    } else {
      params.append('tab', tab);
    }

    return `?${params.toString()}`;
  };

  return (
    <ToolbarItem className={tabClasses()}>
      <Link to={{ pathname: `${match.url}`, search: updateTab(), state: { breadcrumb } }} replace={tab === currentTab}>
        {children}
      </Link>
    </ToolbarItem>
  );
};

const OrganizationDetail = ({
  location,
  match,
  parentBreadcrumbObj,
  organization,
  params,
  currentTab
}) => {
  // TODO: set objectName by param or through grabbing org detail get from api
  const { medium } = PageSectionVariants;

  const deleteResourceView = () => (
    <Fragment>
      {`deleting ${currentTab} association with orgs  `}
      <Link to={{ pathname: `${match.url}`, search: `?${params.toString()}`, state: { breadcrumb: parentBreadcrumbObj, organization } }}>
        {`confirm removal of ${currentTab}/cancel and go back to ${currentTab} view.`}
      </Link>
    </Fragment>
  );

  const addResourceView = () => (
    <Fragment>
      {`adding ${currentTab}   `}
      <Link to={{ pathname: `${match.url}`, search: `?${params.toString()}`, state: { breadcrumb: parentBreadcrumbObj, organization } }}>
        {`save/cancel and go back to ${currentTab} view`}
      </Link>
    </Fragment>
  );

  const resourceView = () => (
    <Fragment>
      {`${currentTab} detail view  `}
      <Link to={{ pathname: `${match.url}/add-resource`, search: `?${params.toString()}`, state: { breadcrumb: parentBreadcrumbObj, organization } }}>
        {`add ${currentTab}`}
      </Link>
      {'  '}
      <Link to={{ pathname: `${match.url}/delete-resources`, search: `?${params.toString()}`, state: { breadcrumb: parentBreadcrumbObj, organization } }}>
        {`delete ${currentTab}`}
      </Link>
    </Fragment>
  );

  const detailTabs = (tabs) => (
    <ToolbarSection aria-label="Organization detail tabs">
      <ToolbarGroup className="at-c-tabs">
        {tabs.map(tab => (
          <DetailTab
            key={tab}
            tab={tab}
            location={location}
            match={match}
            currentTab={currentTab}
            breadcrumb={parentBreadcrumbObj}
          >
            {getTabName(tab)}
          </DetailTab>
        ))}
      </ToolbarGroup>
    </ToolbarSection>
  );

  return (
    <PageSection variant={medium}>
      <Card className="at-c-orgPane">
        <CardHeader>
          {detailTabs(['details', 'users', 'teams', 'admins', 'notifications'])}
        </CardHeader>
        <CardBody>
          {(currentTab && currentTab !== 'details') ? (
            <Switch>
              <Route path={`${match.path}/delete-resources`} component={() => deleteResourceView()} />
              <Route path={`${match.path}/add-resource`} component={() => addResourceView()} />
              <Route path={`${match.path}`} component={() => resourceView()} />
            </Switch>
          ) : (
            <Fragment>
              {'detail view  '}
              <Link to={{ pathname: `${match.url}/edit`, state: { breadcrumb: parentBreadcrumbObj, organization } }}>
                {'edit'}
              </Link>
            </Fragment>
          )}
        </CardBody>
      </Card>
    </PageSection>
  );
};

export default OrganizationDetail;
