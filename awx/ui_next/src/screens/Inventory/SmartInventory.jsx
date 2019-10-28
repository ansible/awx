import React, { Component } from 'react';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import { Card, CardHeader, PageSection } from '@patternfly/react-core';
import { Switch, Route, Redirect, withRouter, Link } from 'react-router-dom';
import CardCloseButton from '@components/CardCloseButton';
import ContentError from '@components/ContentError';
import RoutedTabs from '@components/RoutedTabs';
import { ResourceAccessList } from '@components/ResourceAccessList';
import SmartInventoryDetail from './SmartInventoryDetail';
import SmartInventoryHosts from './SmartInventoryHosts';
import SmartInventoryCompletedJobs from './SmartInventoryCompletedJobs';
import { InventoriesAPI } from '@api';
import SmartInventoryEdit from './SmartInventoryEdit';

class SmartInventory extends Component {
  constructor(props) {
    super(props);

    this.state = {
      contentError: null,
      hasContentLoading: true,
      inventory: null,
    };
    this.loadSmartInventory = this.loadSmartInventory.bind(this);
  }

  async componentDidMount() {
    await this.loadSmartInventory();
  }

  async componentDidUpdate(prevProps) {
    const { location, match } = this.props;
    const url = `/inventories/smart_inventory/${match.params.id}/`;

    if (
      prevProps.location.pathname.startsWith(url) &&
      prevProps.location !== location &&
      location.pathname === `${url}details`
    ) {
      await this.loadSmartInventory();
    }
  }

  async loadSmartInventory() {
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
      { name: i18n._(t`Hosts`), link: `${match.url}/hosts`, id: 2 },
      {
        name: i18n._(t`Completed Jobs`),
        link: `${match.url}/completed_jobs`,
        id: 3,
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
              from="/inventories/smart_inventory/:id"
              to="/inventories/smart_inventory/:id/details"
              exact
            />
            {inventory && [
              <Route
                key="details"
                path="/inventories/smart_inventory/:id/details"
                render={() => (
                  <SmartInventoryDetail
                    match={match}
                    hasSmartInventoryLoading={hasContentLoading}
                    inventory={inventory}
                  />
                )}
              />,
              <Route
                key="edit"
                path="/inventories/smart_inventory/:id/edit"
                render={() => <SmartInventoryEdit inventory={inventory} />}
              />,
              <Route
                key="access"
                path="/inventories/smart_inventory/:id/access"
                render={() => (
                  <ResourceAccessList
                    resource={inventory}
                    apiModel={InventoriesAPI}
                  />
                )}
              />,
              <Route
                key="hosts"
                path="/inventories/smart_inventory/:id/hosts"
                render={() => <SmartInventoryHosts inventory={inventory} />}
              />,
              <Route
                key="completed_jobs"
                path="/inventories/smart_inventory/:id/completed_jobs"
                render={() => (
                  <SmartInventoryCompletedJobs inventory={inventory} />
                )}
              />,
              <Route
                key="not-found"
                path="*"
                render={() =>
                  !hasContentLoading && (
                    <ContentError isNotFound>
                      {match.params.id && (
                        <Link
                          to={`/inventories/smart_inventory/${match.params.id}/details`}
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

export { SmartInventory as _SmartInventory };
export default withI18n()(withRouter(SmartInventory));
