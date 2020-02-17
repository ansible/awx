import React, { useEffect, useState } from 'react';
import { Link, useHistory, useRouteMatch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button, Chip, ChipGroup } from '@patternfly/react-core';
import { OrganizationsAPI } from '@api';
import { DetailList, Detail, UserDateDetail } from '@components/DetailList';
import { CardBody, CardActionsRow } from '@components/Card';
import AlertModal from '@components/AlertModal';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import DeleteButton from '@components/DeleteButton';
import ErrorDetail from '@components/ErrorDetail';

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
  } = organization;
  const [contentError, setContentError] = useState(null);
  const [deletionError, setDeletionError] = useState(null);
  const [hasContentLoading, setHasContentLoading] = useState(true);
  const [instanceGroups, setInstanceGroups] = useState([]);
  const history = useHistory();

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

  const handleDelete = async () => {
    setHasContentLoading(true);
    try {
      await OrganizationsAPI.destroy(id);
      history.push(`/organizations`);
    } catch (error) {
      setDeletionError(error);
    }
    setHasContentLoading(false);
  };

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
        <Detail label={i18n._(t`Max Hosts`)} value={`${max_hosts}`} />
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
              <ChipGroup numChips={5}>
                {instanceGroups.map(ig => (
                  <Chip key={ig.id} isReadOnly>
                    {ig.name}
                  </Chip>
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
              onConfirm={handleDelete}
            >
              {i18n._(t`Delete`)}
            </DeleteButton>
          )}
      </CardActionsRow>
      {/* Update delete modal to show dependencies https://github.com/ansible/awx/issues/5546 */}
      {deletionError && (
        <AlertModal
          isOpen={deletionError}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={() => setDeletionError(null)}
        >
          {i18n._(t`Failed to delete organization.`)}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      )}
    </CardBody>
  );
}

export default withI18n()(OrganizationDetail);
