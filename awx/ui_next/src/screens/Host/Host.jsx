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
import { CaretLeftIcon } from '@patternfly/react-icons';
import { Card, PageSection } from '@patternfly/react-core';
import RoutedTabs from '../../components/RoutedTabs';
import ContentError from '../../components/ContentError';
import ContentLoading from '../../components/ContentLoading';
import JobList from '../../components/JobList';
import HostFacts from './HostFacts';
import HostDetail from './HostDetail';
import HostEdit from './HostEdit';
import HostGroups from './HostGroups';
import { HostsAPI } from '../../api';

function Host({ i18n, setBreadcrumb }) {
  const [host, setHost] = useState(null);
  const [contentError, setContentError] = useState(null);
  const [hasContentLoading, setHasContentLoading] = useState(true);

  const location = useLocation();
  const match = useRouteMatch('/hosts/:id');

  useEffect(() => {
    (async () => {
      setContentError(null);
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
  }, [match.params.id, location, setBreadcrumb]);

  const tabsArray = [
    {
      name: (
        <>
          <CaretLeftIcon />
          {i18n._(t`Back to Hosts`)}
        </>
      ),
      link: `/hosts`,
      id: 99,
    },
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

  if (hasContentLoading) {
    return (
      <PageSection>
        <Card>
          <ContentLoading />
        </Card>
      </PageSection>
    );
  }

  if (contentError) {
    return (
      <PageSection>
        <Card>
          <ContentError error={contentError}>
            {contentError?.response?.status === 404 && (
              <span>
                {i18n._(t`Host not found.`)}{' '}
                <Link to="/hosts">{i18n._(t`View all Hosts.`)}</Link>
              </span>
            )}
          </ContentError>
        </Card>
      </PageSection>
    );
  }

  let showCardHeader = true;

  if (location.pathname.endsWith('edit')) {
    showCardHeader = false;
  }

  return (
    <PageSection>
      <Card>
        {showCardHeader && <RoutedTabs tabsArray={tabsArray} />}
        <Switch>
          <Redirect from="/hosts/:id" to="/hosts/:id/details" exact />
          {host && [
            <Route path="/hosts/:id/details" key="details">
              <HostDetail host={host} />
            </Route>,
            <Route path="/hosts/:id/edit" key="edit">
              <HostEdit host={host} />
            </Route>,
            <Route key="facts" path="/hosts/:id/facts">
              <HostFacts host={host} />
            </Route>,
            <Route path="/hosts/:id/groups" key="groups">
              <HostGroups host={host} />
            </Route>,
            <Route path="/hosts/:id/completed_jobs" key="completed-jobs">
              <JobList defaultParams={{ job__hosts: host.id }} />
            </Route>,
          ]}
          <Route key="not-found" path="*">
            <ContentError isNotFound>
              <Link to={`${match.url}/details`}>
                {i18n._(t`View Host Details`)}
              </Link>
            </ContentError>
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default withI18n()(Host);
export { Host as _Host };
