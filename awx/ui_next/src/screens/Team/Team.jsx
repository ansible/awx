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
import { Card, CardActions, PageSection } from '@patternfly/react-core';
import CardCloseButton from '@components/CardCloseButton';
import { TabbedCardHeader } from '@components/Card';
import RoutedTabs from '@components/RoutedTabs';
import ContentError from '@components/ContentError';
import TeamDetail from './TeamDetail';
import TeamEdit from './TeamEdit';
import { TeamsAPI } from '@api';

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
    { name: i18n._(t`Details`), link: `/teams/${id}/details`, id: 0 },
    { name: i18n._(t`Users`), link: `/teams/${id}/users`, id: 1 },
    { name: i18n._(t`Access`), link: `/teams/${id}/access`, id: 2 },
  ];

  let cardHeader = (
    <TabbedCardHeader>
      <RoutedTabs tabsArray={tabsArray} />
      <CardActions>
        <CardCloseButton linkTo="/teams" />
      </CardActions>
    </TabbedCardHeader>
  );

  if (location.pathname.endsWith('edit')) {
    cardHeader = null;
  }

  if (!hasContentLoading && contentError) {
    return (
      <PageSection>
        <Card>
          <ContentError error={contentError}>
            {contentError.response.status === 404 && (
              <span>
                {i18n._(`Team not found.`)}{' '}
                <Link to="/teams">{i18n._(`View all Teams.`)}</Link>
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
        {cardHeader}
        <Switch>
          <Redirect from="/teams/:id" to="/teams/:id/details" exact />
          {team && (
            <Route path="/teams/:id/details">
              <TeamDetail team={team} />
            </Route>
          )}
          {team && (
            <Route
              path="/teams/:id/edit"
              render={() => <TeamEdit team={team} />}
            />
          )}
          {team && (
            <Route
              path="/teams/:id/users"
              render={() => <span>Coming soon :)</span>}
            />
          )}
          {team && (
            <Route
              path="/teams/:id/access"
              render={() => <span>Coming soon :)</span>}
            />
          )}
          <Route
            key="not-found"
            path="*"
            render={() =>
              !hasContentLoading && (
                <ContentError isNotFound>
                  {id && (
                    <Link to={`/teams/${id}/details`}>
                      {i18n._(`View Team Details`)}
                    </Link>
                  )}
                </ContentError>
              )
            }
          />
        </Switch>
      </Card>
    </PageSection>
  );
}

export default withI18n()(Team);
export { Team as _Team };
