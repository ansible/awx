import React from 'react';
import { t } from '@lingui/macro';

import { Switch, Route, Redirect, Link, useRouteMatch } from 'react-router-dom';
import { CaretLeftIcon } from '@patternfly/react-icons';
import { Card, PageSection } from '@patternfly/react-core';
import ContentError from 'components/ContentError';
import RoutedTabs from 'components/RoutedTabs';
import InstanceDetail from './InstanceDetail';

function Instance({ setBreadcrumb }) {
  const match = useRouteMatch();
  const tabsArray = [
    {
      name: (
        <>
          <CaretLeftIcon />
          {t`Back to Instances`}
        </>
      ),
      link: `/instances`,
      id: 99,
    },
    { name: t`Details`, link: `${match.url}/details`, id: 0 },
  ];

  return (
    <PageSection>
      <Card>
        <RoutedTabs tabsArray={tabsArray} />
        <Switch>
          <Redirect from="/instances/:id" to="/instances/:id/details" exact />
          <Route path="/instances/:id/details" key="details">
            <InstanceDetail setBreadcrumb={setBreadcrumb} />
          </Route>
          <Route path="*" key="not-found">
            <ContentError isNotFound>
              {match.params.id && (
                <Link to={`/instances/${match.params.id}/details`}>
                  {t`View Instance Details`}
                </Link>
              )}
            </ContentError>
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default Instance;
