import React, { Fragment } from 'react';
import { I18n } from '@lingui/react';
import { Trans, t } from '@lingui/macro';
import {
  Card,
  CardHeader,
  CardBody,
  PageSection,
  PageSectionVariants
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
    let classes = 'pf-c-tabs__item';
    if (tab === currentTab) {
      classes += ' pf-m-current';
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
    <li className={tabClasses()}>
        <Link
          className={'pf-c-tabs__button'}
          to={{ pathname: `${match.url}`, search: updateTab(), state: { breadcrumb } }}
          replace={tab === currentTab}>
          {children}
        </Link>
    </li>
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

  const resourceView = () => (
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

  const detailTabs = (tabs) => (
    <I18n>
      {({ i18n }) => (
        <div className="pf-c-tabs" aria-label={i18n._(t`Organization detail tabs`)}>
          <ul className="pf-c-tabs__list">
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
          </ul>
        </div>
      )}
    </I18n>
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
