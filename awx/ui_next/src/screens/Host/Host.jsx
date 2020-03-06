import React, { useEffect, useState } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Switch,
  Route,
  Redirect,
  Link,
  useRouteMatch,
  useLocation,
} from 'react-router-dom';
import { Card, CardActions } from '@patternfly/react-core';

import { TabbedCardHeader } from '@components/Card';
import CardCloseButton from '@components/CardCloseButton';
import RoutedTabs from '@components/RoutedTabs';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import JobList from '@components/JobList';
import HostFacts from './HostFacts';
import HostDetail from './HostDetail';
import HostEdit from './HostEdit';
import HostGroups from './HostGroups';
import { HostsAPI } from '@api';

function Host({ i18n, setBreadcrumb }) {
  const [host, setHost] = useState(null);
  const [contentError, setContentError] = useState(null);
  const [hasContentLoading, setHasContentLoading] = useState(true);

  const location = useLocation();
  const match = useRouteMatch('/hosts/:id');

  useEffect(() => {
    (async () => {
      setContentError(null);
      setHasContentLoading(true);

      try {
        const { data } = await HostsAPI.readDetail(match.params.id);

        setHost(data);
        setBreadcrumb(data);
      } catch (error) {
        setContentError(error);
      } finally {
        setHasContentLoading(false);
      }
    })();
  }, [location]); // eslint-disable-line react-hooks/exhaustive-deps

  const tabsArray = [
    {
      name: i18n._(t`Details`),
      link: `${match.url}/details`,
      id: 0,
    },
    {
      name: i18n._(t`Facts`),
      link: `${match.url}/facts`,
      id: 1,
    },
    {
      name: i18n._(t`Groups`),
      link: `${match.url}/groups`,
      id: 2,
    },
    {
      name: i18n._(t`Completed Jobs`),
      link: `${match.url}/completed_jobs`,
      id: 3,
    },
  ];

  let cardHeader = (
    <TabbedCardHeader>
      <RoutedTabs tabsArray={tabsArray} />
      <CardActions>
        <CardCloseButton linkTo="/hosts" />
      </CardActions>
    </TabbedCardHeader>
  );

  if (location.pathname.endsWith('edit')) {
    cardHeader = null;
  }

  if (hasContentLoading) {
    return <ContentLoading />;
  }

  if (!hasContentLoading && contentError) {
    return (
      <Card>
        <ContentError error={contentError}>
          {contentError.response && contentError.response.status === 404 && (
            <span>
              {i18n._(`Host not found.`)}{' '}
              <Link to="/hosts">{i18n._(`View all Hosts.`)}</Link>
            </span>
          )}
        </ContentError>
      </Card>
    );
  }

  return (
    <Card>
      {cardHeader}
      <Switch>
        <Redirect from="/hosts/:id" to="/hosts/:id/details" exact />
        {host && [
          <Route path="/hosts/:id/details" key="details">
            <HostDetail host={host} />
          </Route>,
          <Route path="/hosts/:id/edit" key="edit">
            <HostEdit host={host} />
          </Route>,
          <Route path="/hosts/:id/facts" key="facts">
            <HostFacts host={host} />
          </Route>,
          <Route path="/hosts/:id/groups" key="groups">
            <HostGroups host={host} />
          </Route>,
          <Route path="/hosts/:id/completed_jobs" key="completed-jobs">
            <JobList defaultParams={{ job__hosts: host.id }} />
          </Route>,
        ]}
        <Route
          key="not-found"
          path="*"
          render={() =>
            !hasContentLoading && (
              <ContentError isNotFound>
                <Link to={`${match.url}/details`}>
                  {i18n._(`View Host Details`)}
                </Link>
              </ContentError>
            )
          }
        />
      </Switch>
    </Card>
  );
}

export default withI18n()(Host);
export { Host as _Host };
