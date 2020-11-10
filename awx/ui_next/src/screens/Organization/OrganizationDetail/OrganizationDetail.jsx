import React, { useEffect, useState, useCallback } from 'react';
import { Link, useHistory, useRouteMatch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button, Chip } from '@patternfly/react-core';
import { OrganizationsAPI } from '../../../api';
import {
  DetailList,
  Detail,
  UserDateDetail,
} from '../../../components/DetailList';
import { CardBody, CardActionsRow } from '../../../components/Card';
import AlertModal from '../../../components/AlertModal';
import ChipGroup from '../../../components/ChipGroup';
import CredentialChip from '../../../components/CredentialChip';
import ContentError from '../../../components/ContentError';
import ContentLoading from '../../../components/ContentLoading';
import DeleteButton from '../../../components/DeleteButton';
import ErrorDetail from '../../../components/ErrorDetail';
import useRequest, { useDismissableError } from '../../../util/useRequest';
import { useConfig } from '../../../contexts/Config';

function OrganizationDetail({ i18n, organization }) {
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

  if (hasContentLoading) {
    return <ContentLoading />;
  }

  if (contentError) {
    return <ContentError error={contentError} />;
  }

  return (
    <CardBody>
      <DetailList>
        <Detail
          label={i18n._(t`Name`)}
          value={name}
          dataCy="organization-detail-name"
        />
        <Detail label={i18n._(t`Description`)} value={description} />
        {license_info?.license_type !== 'open' && (
          <Detail label={i18n._(t`Max Hosts`)} value={`${max_hosts}`} />
        )}
        <Detail
          label={i18n._(t`Ansible Environment`)}
          value={custom_virtualenv}
        />
        <UserDateDetail
          label={i18n._(t`Created`)}
          date={created}
          user={summary_fields.created_by}
        />
        <UserDateDetail
          label={i18n._(t`Last Modified`)}
          date={modified}
          user={summary_fields.modified_by}
        />
        {instanceGroups && instanceGroups.length > 0 && (
          <Detail
            fullWidth
            label={i18n._(t`Instance Groups`)}
            value={
              <ChipGroup numChips={5} totalChips={instanceGroups.length}>
                {instanceGroups.map(ig => (
                  <Chip key={ig.id} isReadOnly>
                    {ig.name}
                  </Chip>
                ))}
              </ChipGroup>
            }
          />
        )}
        {galaxy_credentials && galaxy_credentials.length > 0 && (
          <Detail
            fullWidth
            label={i18n._(t`Galaxy Credentials`)}
            value={
              <ChipGroup numChips={5} totalChips={galaxy_credentials.length}>
                {galaxy_credentials.map(credential => (
                  <CredentialChip
                    credential={credential}
                    key={credential.id}
                    isReadOnly
                  />
                ))}
              </ChipGroup>
            }
          />
        )}
      </DetailList>
      <CardActionsRow>
        {summary_fields.user_capabilities.edit && (
          <Button
            aria-label={i18n._(t`Edit`)}
            component={Link}
            to={`/organizations/${id}/edit`}
          >
            {i18n._(t`Edit`)}
          </Button>
        )}
        {summary_fields.user_capabilities &&
          summary_fields.user_capabilities.delete && (
            <DeleteButton
              name={name}
              modalTitle={i18n._(t`Delete Organization`)}
              onConfirm={deleteOrganization}
              isDisabled={isLoading}
            >
              {i18n._(t`Delete`)}
            </DeleteButton>
          )}
      </CardActionsRow>
      {/* Update delete modal to show dependencies https://github.com/ansible/awx/issues/5546 */}
      {error && (
        <AlertModal
          isOpen={error}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={dismissError}
        >
          {i18n._(t`Failed to delete organization.`)}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </CardBody>
  );
}

export default withI18n()(OrganizationDetail);
