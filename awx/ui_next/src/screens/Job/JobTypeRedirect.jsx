import React, { useCallback, useEffect } from 'react';
import { Redirect, Link } from 'react-router-dom';
import { PageSection, Card } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import useRequest from '../../util/useRequest';
import { UnifiedJobsAPI } from '../../api';
import ContentError from '../../components/ContentError';
import { JOB_TYPE_URL_SEGMENTS } from '../../constants';

const NOT_FOUND = 'not found';

function JobTypeRedirect({ id, path, view, i18n }) {
  const {
    isLoading,
    error,
    result: { job },
    request: loadJob,
  } = useRequest(
    useCallback(async () => {
      const { data } = await UnifiedJobsAPI.read({ id });
      return { job: data };
    }, [id]),
    { job: {} }
  );
  useEffect(() => {
    loadJob();
  }, [loadJob]);

  if (error) {
    return (
      <PageSection>
        <Card>
          {error === NOT_FOUND ? (
            <ContentError isNotFound>
              <Link to="/jobs">{i18n._(t`View all Jobs`)}</Link>
            </ContentError>
          ) : (
            <ContentError error={error} />
          )}
        </Card>
      </PageSection>
    );
  }
  if (isLoading) {
    // TODO show loading state
    return <div>Loading...</div>;
  }
  const type = JOB_TYPE_URL_SEGMENTS[job.type];
  return <Redirect from={path} to={`/jobs/${type}/${job.id}/${view}`} />;
}

JobTypeRedirect.defaultProps = {
  view: 'output',
};
export default withI18n()(JobTypeRedirect);
