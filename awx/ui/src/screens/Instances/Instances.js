import React, { useCallback, useState } from 'react';
import { t } from '@lingui/macro';
import { Route, Switch, Redirect, useRouteMatch, Link } from 'react-router-dom';
import { Card, PageSection } from '@patternfly/react-core';

import { getQSConfig } from 'util/qs';
import ContentError from 'components/ContentError';
import ScreenHeader from 'components/ScreenHeader';
import { HeaderRow, HeaderCell } from 'components/PaginatedTable';
import { InstanceList } from 'components/Instances';
import InstanceDetail from 'components/InstanceDetail';

const QS_CONFIG = getQSConfig('instance', {
  page: 1,
  page_size: 20,
  order_by: 'hostname',
});
function Instances() {
  const match = useRouteMatch();
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/instances': t`Instances`,
  });

  const buildBreadcrumbConfig = useCallback((instance) => {
    if (!instance) {
      return;
    }
    setBreadcrumbConfig({
      '/instances': t`Instances`,
      [`/instances/${instance.id}`]: `${instance.hostname}`,
      [`/instances/${instance.id}/details`]: t`Details`,
    });
  }, []);

  return (
    <>
      <ScreenHeader
        streamType="instances"
        breadcrumbConfig={breadcrumbConfig}
      />
      <PageSection>
        <Card>
          <Switch>
            <Redirect from="/instances/:id" to="/instances/:id/details" exact />
            <Route key="details" path="/instances/:id/details">
              <InstanceDetail setBreadcrumb={buildBreadcrumbConfig} />
            </Route>
            <Route path="/instances">
              <InstanceList
                QS_CONFIG={QS_CONFIG}
                headerRow={
                  <HeaderRow qsConfig={QS_CONFIG} isExpandable>
                    <HeaderCell sortKey="hostname">{t`Name`}</HeaderCell>
                    <HeaderCell sortKey="errors">{t`Status`}</HeaderCell>
                    <HeaderCell sortKey="node_type">{t`Node Type`}</HeaderCell>
                    <HeaderCell sortKey="capacity_adjustment">{t`Capacity Adjustment`}</HeaderCell>
                    <HeaderCell>{t`Used Capacity`}</HeaderCell>
                    <HeaderCell sortKey="enabled">{t`Actions`}</HeaderCell>
                  </HeaderRow>
                }
              />
            </Route>
            ,
            <Route path="*" key="not-found">
              <ContentError isNotFound>
                {match.params.id && (
                  <Link to="/instances">{t`View Instances`}</Link>
                )}
              </ContentError>
            </Route>
          </Switch>
        </Card>
      </PageSection>
    </>
  );
}

export default Instances;
