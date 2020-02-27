import React, { useEffect, useState } from 'react';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import {
  Switch,
  Route,
  Redirect,
  Link,
  useLocation,
  useRouteMatch,
} from 'react-router-dom';

import { Card, CardActions, PageSection } from '@patternfly/react-core';
import { TabbedCardHeader } from '@components/Card';
import CardCloseButton from '@components/CardCloseButton';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import JobList from '@components/JobList';
import RoutedTabs from '@components/RoutedTabs';
import { ResourceAccessList } from '@components/ResourceAccessList';
import InventoryDetail from './InventoryDetail';
import InventoryEdit from './InventoryEdit';
import InventoryGroups from './InventoryGroups';
import InventoryHosts from './InventoryHosts/InventoryHosts';
import InventorySources from './InventorySources';
import { InventoriesAPI } from '@api';

function Inventory({ i18n, setBreadcrumb }) {
  const [contentError, setContentError] = useState(null);
  const [hasContentLoading, setHasContentLoading] = useState(true);
  const [inventory, setInventory] = useState(null);
  const location = useLocation();
  const match = useRouteMatch({
    path: '/inventories/inventory/:id',
  });

  useEffect(() => {
    async function fetchData() {
      try {
        const { data } = await InventoriesAPI.readDetail(match.params.id);
        setBreadcrumb(data);
        setInventory(data);
      } catch (error) {
        setContentError(error);
      } finally {
        setHasContentLoading(false);
      }
    }

    fetchData();
  }, [match.params.id, location.pathname, setBreadcrumb]);

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
    <TabbedCardHeader>
      <RoutedTabs tabsArray={tabsArray} />
      <CardActions>
        <CardCloseButton linkTo="/inventories" />
      </CardActions>
    </TabbedCardHeader>
  );

  if (
    location.pathname.endsWith('edit') ||
    location.pathname.endsWith('add') ||
    location.pathname.includes('groups/') ||
    location.pathname.includes('hosts/')
  ) {
    cardHeader = null;
  }

  if (hasContentLoading) {
    return (
      <PageSection>
        <Card>
          <ContentLoading />
        </Card>
      </PageSection>
    );
  }

  if (!hasContentLoading && contentError) {
    return (
      <PageSection>
        <Card>
          <ContentError error={contentError}>
            {contentError.response.status === 404 && (
              <span>
                {i18n._(`Inventory not found.`)}{' '}
                <Link to="/inventories">{i18n._(`View all Inventories.`)}</Link>
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
              key="hosts"
              path="/inventories/inventory/:id/hosts"
              render={() => (
                <InventoryHosts
                  setBreadcrumb={setBreadcrumb}
                  inventory={inventory}
                />
              )}
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
              render={() => (
                <InventoryGroups
                  setBreadcrumb={setBreadcrumb}
                  inventory={inventory}
                />
              )}
            />,
            <Route
              key="sources"
              path="/inventories/inventory/:id/sources"
              render={() => <InventorySources inventory={inventory} />}
            />,
            <Route
              key="completed_jobs"
              path="/inventories/inventory/:id/completed_jobs"
            >
              <JobList
                defaultParams={{
                  or__job__inventory: inventory.id,
                  or__adhoccommand__inventory: inventory.id,
                  or__inventoryupdate__inventory_source__inventory:
                    inventory.id,
                  or__workflowjob__inventory: inventory.id,
                }}
              />
            </Route>,
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

export { Inventory as _Inventory };
export default withI18n()(Inventory);
