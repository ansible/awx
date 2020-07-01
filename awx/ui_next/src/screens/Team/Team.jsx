import React, { useState, useEffect } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Link,
  Redirect,
  Route,
  Switch,
  useLocation,
  useParams,
} from 'react-router-dom';
import { CaretLeftIcon } from '@patternfly/react-icons';
import { Card, PageSection } from '@patternfly/react-core';
import RoutedTabs from '../../components/RoutedTabs';
import ContentError from '../../components/ContentError';
import TeamDetail from './TeamDetail';
import TeamEdit from './TeamEdit';
import { TeamsAPI } from '../../api';
import TeamAccessList from './TeamAccess';

function Team({ i18n, setBreadcrumb }) {
  const [team, setTeam] = useState(null);
  const [contentError, setContentError] = useState(null);
  const [hasContentLoading, setHasContentLoading] = useState(true);
  const location = useLocation();
  const { id } = useParams();

  useEffect(() => {
    (async () => {
      try {
        const { data } = await TeamsAPI.readDetail(id);
        setBreadcrumb(data);
        setTeam(data);
      } catch (error) {
        setContentError(error);
      } finally {
        setHasContentLoading(false);
      }
    })();
  }, [id, setBreadcrumb, location]);

  const tabsArray = [
    {
      name: (
        <>
          <CaretLeftIcon />
          {i18n._(t`Back to Teams`)}
        </>
      ),
      link: `/teams`,
      id: 99,
    },
    { name: i18n._(t`Details`), link: `/teams/${id}/details`, id: 0 },
    { name: i18n._(t`Users`), link: `/teams/${id}/users`, id: 1 },
    { name: i18n._(t`Access`), link: `/teams/${id}/access`, id: 2 },
  ];

  let showCardHeader = true;

  if (location.pathname.endsWith('edit')) {
    showCardHeader = false;
  }

  if (!hasContentLoading && contentError) {
    return (
      <PageSection>
        <Card>
          <ContentError error={contentError}>
            {contentError.response.status === 404 && (
              <span>
                {i18n._(t`Team not found.`)}{' '}
                <Link to="/teams">{i18n._(t`View all Teams.`)}</Link>
              </span>
            )}
          </ContentError>
        </Card>
      </PageSection>
    );
  }

  return (
    <PageSection>
      <Card>
        {showCardHeader && <RoutedTabs tabsArray={tabsArray} />}
        <Switch>
          <Redirect from="/teams/:id" to="/teams/:id/details" exact />
          {team && (
            <Route path="/teams/:id/details">
              <TeamDetail team={team} />
            </Route>
          )}
          {team && (
            <Route path="/teams/:id/edit">
              <TeamEdit team={team} />
            </Route>
          )}
          {team && (
            <Route path="/teams/:id/users">
              <span>Coming soon :)</span>
            </Route>
          )}
          {team && (
            <Route path="/teams/:id/access">
              <TeamAccessList />
            </Route>
          )}
          <Route key="not-found" path="*">
            {!hasContentLoading && (
              <ContentError isNotFound>
                {id && (
                  <Link to={`/teams/${id}/details`}>
                    {i18n._(t`View Team Details`)}
                  </Link>
                )}
              </ContentError>
            )}
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default withI18n()(Team);
export { Team as _Team };
