import React, { useCallback, useEffect } from 'react';
import { Redirect, Link } from 'react-router-dom';
import { PageSection, Card } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import useRequest from '../../util/useRequest';
import { UnifiedJobsAPI } from '../../api';
import ContentError from '../../components/ContentError';
import ContentLoading from '../../components/ContentLoading';
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
      const {
        data: { results },
      } = await UnifiedJobsAPI.read({ id });
      const [item] = results;
      return { job: item };
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
  if (isLoading || !job?.id) {
    return (
      <PageSection>
        <Card>
          <ContentLoading />
        </Card>
      </PageSection>
    );
  }
  const type = JOB_TYPE_URL_SEGMENTS[job.type];
  return <Redirect from={path} to={`/jobs/${type}/${job.id}/${view}`} />;
}

JobTypeRedirect.defaultProps = {
  view: 'output',
};
export default withI18n()(JobTypeRedirect);
