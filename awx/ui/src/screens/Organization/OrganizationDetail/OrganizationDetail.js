import React, { useEffect, useState, useCallback } from 'react';
import { Link, useHistory, useRouteMatch } from 'react-router-dom';

import { t } from '@lingui/macro';
import { Button, Chip } from '@patternfly/react-core';
import { OrganizationsAPI } from 'api';
import { DetailList, Detail, UserDateDetail } from 'components/DetailList';
import { CardBody, CardActionsRow } from 'components/Card';
import AlertModal from 'components/AlertModal';
import ChipGroup from 'components/ChipGroup';
import CredentialChip from 'components/CredentialChip';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import DeleteButton from 'components/DeleteButton';
import ErrorDetail from 'components/ErrorDetail';
import useRequest, { useDismissableError } from 'hooks/useRequest';
import { useConfig } from 'contexts/Config';
import ExecutionEnvironmentDetail from 'components/ExecutionEnvironmentDetail';
import { relatedResourceDeleteRequests } from 'util/getRelatedResourceDeleteDetails';

function OrganizationDetail({ organization }) {
  const {
    params: { id },
  } = useRouteMatch();
  const {
    name,
    description,
    custom_virtualenv,
    max_hosts,
    created,
    modified,
    summary_fields,
    galaxy_credentials,
  } = organization;
  const [contentError, setContentError] = useState(null);
  const [hasContentLoading, setHasContentLoading] = useState(true);
  const [instanceGroups, setInstanceGroups] = useState([]);
  const history = useHistory();
  const { license_info = {} } = useConfig();

  useEffect(() => {
    (async () => {
      setContentError(null);
      setHasContentLoading(true);
      try {
        const {
          data: { results = [] },
        } = await OrganizationsAPI.readInstanceGroups(id);
        setInstanceGroups(results);
      } catch (error) {
        setContentError(error);
      } finally {
        setHasContentLoading(false);
      }
    })();
  }, [id]);

  const {
    request: deleteOrganization,
    isLoading,
    error: deleteError,
  } = useRequest(
    useCallback(async () => {
      await OrganizationsAPI.destroy(id);
      history.push(`/organizations`);
    }, [id, history])
  );

  const { error, dismissError } = useDismissableError(deleteError);

  const deleteDetailsRequests =
    relatedResourceDeleteRequests.organization(organization);

  if (hasContentLoading) {
    return <ContentLoading />;
  }

  if (contentError) {
    return <ContentError error={contentError} />;
  }

  const buildLinkURL = (instance) =>
    instance.is_container_group
      ? '/instance_groups/container_group/'
      : '/instance_groups/';

  return (
    <CardBody>
      <DetailList>
        <Detail
          label={t`Name`}
          value={name}
          dataCy="organization-detail-name"
        />
        <Detail label={t`Description`} value={description} />
        {license_info?.license_type !== 'open' && (
          <Detail label={t`Max Hosts`} value={`${max_hosts}`} />
        )}
        <ExecutionEnvironmentDetail
          virtualEnvironment={custom_virtualenv}
          executionEnvironment={summary_fields?.default_environment}
          isDefaultEnvironment
        />
        <UserDateDetail
          label={t`Created`}
          date={created}
          user={summary_fields.created_by}
        />
        <UserDateDetail
          label={t`Last Modified`}
          date={modified}
          user={summary_fields.modified_by}
        />
        {instanceGroups && instanceGroups.length > 0 && (
          <Detail
            fullWidth
            label={t`Instance Groups`}
            value={
              <ChipGroup numChips={5} totalChips={instanceGroups.length}>
                {instanceGroups.map((ig) => (
                  <Link to={`${buildLinkURL(ig)}${ig.id}/details`} key={ig.id}>
                    <Chip key={ig.id} isReadOnly>
                      {ig.name}
                    </Chip>
                  </Link>
                ))}
              </ChipGroup>
            }
          />
        )}
        {galaxy_credentials && galaxy_credentials.length > 0 && (
          <Detail
            fullWidth
            label={t`Galaxy Credentials`}
            value={
              <ChipGroup numChips={5} totalChips={galaxy_credentials.length}>
                {galaxy_credentials.map((credential) => (
                  <Link to={`/credentials/${credential.id}/details`}>
                    <CredentialChip
                      credential={credential}
                      key={credential.id}
                      isReadOnly
                    />
                  </Link>
                ))}
              </ChipGroup>
            }
          />
        )}
      </DetailList>
      <CardActionsRow>
        {summary_fields.user_capabilities.edit && (
          <Button
            ouiaId="organization-detail-edit-button"
            aria-label={t`Edit`}
            component={Link}
            to={`/organizations/${id}/edit`}
          >
            {t`Edit`}
          </Button>
        )}
        {summary_fields.user_capabilities &&
          summary_fields.user_capabilities.delete && (
            <DeleteButton
              name={name}
              modalTitle={t`Delete Organization`}
              onConfirm={deleteOrganization}
              isDisabled={isLoading}
              deleteDetailsRequests={deleteDetailsRequests}
              deleteMessage={t`This organization is currently being by other resources. Are you sure you want to delete it?`}
            >
              {t`Delete`}
            </DeleteButton>
          )}
      </CardActionsRow>
      {/* Update delete modal to show dependencies https://github.com/ansible/awx/issues/5546 */}
      {error && (
        <AlertModal
          isOpen={error}
          variant="error"
          title={t`Error!`}
          onClose={dismissError}
        >
          {t`Failed to delete organization.`}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </CardBody>
  );
}

export default OrganizationDetail;
