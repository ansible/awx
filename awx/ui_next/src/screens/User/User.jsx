import React, { Component } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Switch, Route, withRouter, Redirect, Link } from 'react-router-dom';
import {
  Card,
  CardHeader as PFCardHeader,
  PageSection,
} from '@patternfly/react-core';
import styled from 'styled-components';
import CardCloseButton from '@components/CardCloseButton';
import RoutedTabs from '@components/RoutedTabs';
import ContentError from '@components/ContentError';
import UserDetail from './UserDetail';
import UserEdit from './UserEdit';
import UserOrganizations from './UserOrganizations';
import UserTeams from './UserTeams';
import UserTokens from './UserTokens';
import { UsersAPI } from '@api';

const CardHeader = styled(PFCardHeader)`
  --pf-c-card--first-child--PaddingTop: 0;
  --pf-c-card--child--PaddingLeft: 0;
  --pf-c-card--child--PaddingRight: 0;
  position: relative;
`;

class User extends Component {
  constructor(props) {
    super(props);

    this.state = {
      user: null,
      hasContentLoading: true,
      contentError: null,
      isInitialized: false,
    };
    this.loadUser = this.loadUser.bind(this);
  }

  async componentDidMount() {
    await this.loadUser();
    this.setState({ isInitialized: true });
  }

  async componentDidUpdate(prevProps) {
    const { location, match } = this.props;
    const url = `/users/${match.params.id}/`;

    if (
      prevProps.location.pathname.startsWith(url) &&
      prevProps.location !== location &&
      location.pathname === `${url}details`
    ) {
      await this.loadUser();
    }
  }

  async loadUser() {
    const { match, setBreadcrumb } = this.props;
    const id = parseInt(match.params.id, 10);

    this.setState({ contentError: null, hasContentLoading: true });
    try {
      const { data } = await UsersAPI.readDetail(id);
      setBreadcrumb(data);
      this.setState({ user: data });
    } catch (err) {
      this.setState({ contentError: err });
    } finally {
      this.setState({ hasContentLoading: false });
    }
  }

  render() {
    const { location, match, history, i18n } = this.props;

    const { user, contentError, hasContentLoading, isInitialized } = this.state;

    const tabsArray = [
      { name: i18n._(t`Details`), link: `${match.url}/details`, id: 0 },
      {
        name: i18n._(t`Organizations`),
        link: `${match.url}/organizations`,
        id: 1,
      },
      { name: i18n._(t`Teams`), link: `${match.url}/teams`, id: 2 },
      { name: i18n._(t`Access`), link: `${match.url}/access`, id: 3 },
      { name: i18n._(t`Tokens`), link: `${match.url}/tokens`, id: 4 },
    ];

    let cardHeader = (
      <CardHeader style={{ padding: 0 }}>
        <RoutedTabs
          match={match}
          history={history}
          labeltext={i18n._(t`User detail tabs`)}
          tabsArray={tabsArray}
        />
        <CardCloseButton linkTo="/users" />
      </CardHeader>
    );

    if (!isInitialized) {
      cardHeader = null;
    }

    if (!match) {
      cardHeader = null;
    }

    if (location.pathname.endsWith('edit')) {
      cardHeader = null;
    }

    if (!hasContentLoading && contentError) {
      return (
        <PageSection>
          <Card className="awx-c-card">
            <ContentError error={contentError}>
              {contentError.response.status === 404 && (
                <span>
                  {i18n._(`User not found.`)}{' '}
                  <Link to="/users">{i18n._(`View all Users.`)}</Link>
                </span>
              )}
            </ContentError>
          </Card>
        </PageSection>
      );
    }

    return (
      <PageSection>
        <Card className="awx-c-card">
          {cardHeader}
          <Switch>
            <Redirect from="/users/:id" to="/users/:id/details" exact />
            {user && (
              <Route
                path="/users/:id/edit"
                render={() => <UserEdit match={match} user={user} />}
              />
            )}
            {user && (
              <Route
                path="/users/:id/details"
                render={() => <UserDetail match={match} user={user} />}
              />
            )}
            <Route
              path="/users/:id/organizations"
              render={() => <UserOrganizations id={Number(match.params.id)} />}
            />
            <Route
              path="/users/:id/teams"
              render={() => <UserTeams id={Number(match.params.id)} />}
            />
            {user && (
              <Route
                path="/users/:id/access"
                render={() => (
                  <span>
                    this needs a different access list from regular resources
                    like proj, inv, jt
                  </span>
                )}
              />
            )}
            <Route
              path="/users/:id/tokens"
              render={() => <UserTokens id={Number(match.params.id)} />}
            />
            <Route
              key="not-found"
              path="*"
              render={() =>
                !hasContentLoading && (
                  <ContentError isNotFound>
                    {match.params.id && (
                      <Link to={`/users/${match.params.id}/details`}>
                        {i18n._(`View User Details`)}
                      </Link>
                    )}
                  </ContentError>
                )
              }
            />
            ,
          </Switch>
        </Card>
      </PageSection>
    );
  }
}

export default withI18n()(withRouter(User));
export { User as _User };
