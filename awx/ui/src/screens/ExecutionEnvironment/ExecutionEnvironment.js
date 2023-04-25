import React, { useEffect, useCallback } from 'react';
import {
  Link,
  Redirect,
  Route,
  Switch,
  useLocation,
  useParams,
} from 'react-router-dom';

import { t } from '@lingui/macro';
import { Card, PageSection } from '@patternfly/react-core';
import { CaretLeftIcon } from '@patternfly/react-icons';

import useRequest from 'hooks/useRequest';
import { ExecutionEnvironmentsAPI } from 'api';
import RoutedTabs from 'components/RoutedTabs';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';

import ExecutionEnvironmentDetails from './ExecutionEnvironmentDetails';
import ExecutionEnvironmentEdit from './ExecutionEnvironmentEdit';
import ExecutionEnvironmentTemplateList from './ExecutionEnvironmentTemplate';

function ExecutionEnvironment({ setBreadcrumb }) {
  const { id } = useParams();
  const { pathname } = useLocation();

  const {
    isLoading,
    error: contentError,
    request: fetchExecutionEnvironments,
    result: executionEnvironment,
  } = useRequest(
    useCallback(async () => {
      const { data } = await ExecutionEnvironmentsAPI.readDetail(id);
      return data;
    }, [id]),
    null
  );

  useEffect(() => {
    fetchExecutionEnvironments();
  }, [fetchExecutionEnvironments, pathname]);

  useEffect(() => {
    if (executionEnvironment) {
      setBreadcrumb(executionEnvironment);
    }
  }, [executionEnvironment, setBreadcrumb]);

  const tabsArray = [
    {
      name: (
        <>
          <CaretLeftIcon />
          {t`Back to execution environments`}
        </>
      ),
      link: '/execution_environments',
      id: 99,
      persistentFilterKey: 'executionEnvironments',
    },
    {
      name: t`Details`,
      link: `/execution_environments/${id}/details`,
      id: 0,
    },
    {
      name: t`Templates`,
      link: `/execution_environments/${id}/templates`,
      id: 1,
    },
  ];

  if (!isLoading && contentError) {
    return (
      <PageSection>
        <Card>
          <ContentError error={contentError}>
            {contentError.response?.status === 404 && (
              <span>
                {t`Execution environment not found.`}{' '}
                <Link to="/execution_environments">
                  {t`View all execution environments`}
                </Link>
              </span>
            )}
          </ContentError>
        </Card>
      </PageSection>
    );
  }

  let cardHeader = <RoutedTabs tabsArray={tabsArray} />;
  if (pathname.endsWith('edit')) {
    cardHeader = null;
  }

  return (
    <PageSection>
      <Card>
        {cardHeader}
        {isLoading && <ContentLoading />}
        {!isLoading && executionEnvironment && (
          <Switch>
            <Redirect
              from="/execution_environments/:id"
              to="/execution_environments/:id/details"
              exact
            />
            {executionEnvironment && (
              <>
                <Route path="/execution_environments/:id/edit">
                  <ExecutionEnvironmentEdit
                    executionEnvironment={executionEnvironment}
                  />
                </Route>
                <Route path="/execution_environments/:id/details">
                  <ExecutionEnvironmentDetails
                    executionEnvironment={executionEnvironment}
                  />
                </Route>
                <Route path="/execution_environments/:id/templates">
                  <ExecutionEnvironmentTemplateList
                    executionEnvironment={executionEnvironment}
                  />
                </Route>
              </>
            )}
          </Switch>
        )}
      </Card>
    </PageSection>
  );
}

export default ExecutionEnvironment;
