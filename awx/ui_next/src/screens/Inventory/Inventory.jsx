import React, { Component } from 'react';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import { Card, CardHeader, PageSection } from '@patternfly/react-core';
import { Switch, Route, Redirect, withRouter, Link } from 'react-router-dom';
import CardCloseButton from '@components/CardCloseButton';
import ContentError from '@components/ContentError';
import RoutedTabs from '@components/RoutedTabs';
import { ResourceAccessList } from '@components/ResourceAccessList';
import InventoryDetail from './InventoryDetail';
import InventoryHosts from './InventoryHosts';
import InventoryGroups from './InventoryGroups';
import InventoryCompletedJobs from './InventoryCompletedJobs';
import InventorySources from './InventorySources';
import { InventoriesAPI } from '@api';
import InventoryEdit from './InventoryEdit';

class Inventory extends Component {
  constructor(props) {
    super(props);

    this.state = {
      contentError: null,
      hasContentLoading: true,
      inventory: null,
    };
    this.loadInventory = this.loadInventory.bind(this);
  }

  async componentDidMount() {
    await this.loadInventory();
  }

  async componentDidUpdate(prevProps) {
    const { location, match } = this.props;
    const url = `/inventories/inventory/${match.params.id}/`;

    if (
      prevProps.location.pathname.startsWith(url) &&
      prevProps.location !== location &&
      location.pathname === `${url}details`
    ) {
      await this.loadInventory();
    }
  }

  async loadInventory() {
    const { setBreadcrumb, match } = this.props;
    const { id } = match.params;

    this.setState({ contentError: null, hasContentLoading: true });
    try {
      const { data } = await InventoriesAPI.readDetail(id);
      setBreadcrumb(data);
      this.setState({ inventory: data });
    } catch (err) {
      this.setState({ contentError: err });
    } finally {
      this.setState({ hasContentLoading: false });
    }
  }

  render() {
    const { history, i18n, location, match } = this.props;
    const { contentError, hasContentLoading, inventory } = this.state;

    const tabsArray = [
      { name: i18n._(t`Details`), link: `${match.url}/details`, id: 0 },
      { name: i18n._(t`Access`), link: `${match.url}/access`, id: 1 },
      { name: i18n._(t`Groups`), link: `${match.url}/groups`, id: 2 },
      { name: i18n._(t`Hosts`), link: `${match.url}/hosts`, id: 3 },
      { name: i18n._(t`Sources`), link: `${match.url}/sources`, id: 4 },
      {
        name: i18n._(t`Completed Jobs`),
        link: `${match.url}/completed_jobs`,
        id: 5,
      },
    ];

    let cardHeader = hasContentLoading ? null : (
      <CardHeader style={{ padding: 0 }}>
        <RoutedTabs history={history} tabsArray={tabsArray} />
        <CardCloseButton linkTo="/inventories" />
      </CardHeader>
    );

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
                  {i18n._(`Inventory not found.`)}{' '}
                  <Link to="/inventories">
                    {i18n._(`View all Inventories.`)}
                  </Link>
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
            <Redirect
              from="/inventories/inventory/:id"
              to="/inventories/inventory/:id/details"
              exact
            />
            {inventory && [
              <Route
                key="details"
                path="/inventories/inventory/:id/details"
                render={() => (
                  <InventoryDetail
                    match={match}
                    hasInventoryLoading={hasContentLoading}
                    inventory={inventory}
                  />
                )}
              />,
              <Route
                key="edit"
                path="/inventories/inventory/:id/edit"
                render={() => <InventoryEdit inventory={inventory} />}
              />,
              <Route
                key="access"
                path="/inventories/inventory/:id/access"
                render={() => (
                  <ResourceAccessList
                    resource={inventory}
                    apiModel={InventoriesAPI}
                  />
                )}
              />,
              <Route
                key="groups"
                path="/inventories/inventory/:id/groups"
                render={() => <InventoryGroups inventory={inventory} />}
              />,
              <Route
                key="hosts"
                path="/inventories/inventory/:id/hosts"
                render={() => <InventoryHosts inventory={inventory} />}
              />,
              <Route
                key="sources"
                path="/inventories/inventory/:id/sources"
                render={() => <InventorySources inventory={inventory} />}
              />,
              <Route
                key="completed_jobs"
                path="/inventories/inventory/:id/completed_jobs"
                render={() => <InventoryCompletedJobs inventory={inventory} />}
              />,
              <Route
                key="not-found"
                path="*"
                render={() =>
                  !hasContentLoading && (
                    <ContentError isNotFound>
                      {match.params.id && (
                        <Link
                          to={`/inventories/inventory/${match.params.id}/details`}
                        >
                          {i18n._(`View Inventory Details`)}
                        </Link>
                      )}
                    </ContentError>
                  )
                }
              />,
            ]}
          </Switch>
        </Card>
      </PageSection>
    );
  }
}

export { Inventory as _Inventory };
export default withI18n()(withRouter(Inventory));
