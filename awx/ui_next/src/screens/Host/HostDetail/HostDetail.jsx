import React from 'react';
import { Link } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Host } from '@types';
import { Button } from '@patternfly/react-core';
import { CardBody, CardActionsRow } from '@components/Card';
import { DetailList, Detail, UserDateDetail } from '@components/DetailList';
import { VariablesDetail } from '@components/CodeMirrorInput';
import { Sparkline } from '@components/Sparkline';
import Switch from '@components/Switch';

function HostDetail({ host, i18n }) {
const ActionButtonWrapper = styled.div`
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
  & > :not(:first-child) {
    margin-left: 20px;
  }
`;

function HostDetail({
  host,
  history,
  isDeleteModalOpen,
  match,
  i18n,
  toggleError,
  toggleLoading,
  onHostDelete,
  onToggleDeleteModal,
  onToggleError,
  onHandleHostToggle,
}) {
  const { created, description, id, modified, name, summary_fields } = host;
  let createdBy = '';
  if (created) {
    if (summary_fields.created_by && summary_fields.created_by.username) {
      createdBy = (
        <span>
          {i18n._(t`${formatDateString(created)} by `)}{' '}
          <Link to={`/users/${summary_fields.created_by.id}`}>
            {summary_fields.created_by.username}
          </Link>
        </span>
      );
    } else {
      createdBy = formatDateString(created);
    }
  }

  let modifiedBy = '';
  if (modified) {
    if (summary_fields.modified_by && summary_fields.modified_by.username) {
      modifiedBy = (
        <span>
          {i18n._(t`${formatDateString(modified)} by`)}{' '}
          <Link to={`/users/${summary_fields.modified_by.id}`}>
            {summary_fields.modified_by.username}
          </Link>
        </span>
      );
    } else {
      modifiedBy = formatDateString(modified);
    }
  }
  if (toggleError && !toggleLoading) {
    return (
      <AlertModal
        variant="danger"
        title={i18n._(t`Error!`)}
        isOpen={toggleError && !toggleLoading}
        onClose={onToggleError}
      >
        {i18n._(t`Failed to toggle host.`)}
        <ErrorDetail error={toggleError} />
      </AlertModal>
    );
  }
  if (isDeleteModalOpen) {
    return (
      <AlertModal
        isOpen={isDeleteModalOpen}
        title={i18n._(t`Delete Host`)}
        variant="danger"
        onClose={() => onToggleDeleteModal()}
      >
        {i18n._(t`Are you sure you want to delete:`)}
        <br />
        <strong>{host.name}</strong>
        <ActionButtonWrapper>
          <Button
            variant="secondary"
            aria-label={i18n._(t`Close`)}
            onClick={() => onToggleDeleteModal()}
          >
            {i18n._(t`Cancel`)}
          </Button>

          <Button
            variant="danger"
            aria-label={i18n._(t`Delete`)}
            onClick={() => onHostDelete()}
          >
            {i18n._(t`Delete`)}
          </Button>
        </ActionButtonWrapper>
      </AlertModal>
    );
  }
  return (
    <CardBody>
      <Switch
        css="padding-bottom: 40px; padding-top: 20px"
        id={`host-${host.id}-toggle`}
        label={i18n._(t`On`)}
        labelOff={i18n._(t`Off`)}
        isChecked={host.enabled}
        isDisabled={!host.summary_fields.user_capabilities.edit}
        onChange={onHandleHostToggle}
        aria-label={i18n._(t`Toggle Host`)}
      />
      <DetailList gutter="sm">
        <Detail label={i18n._(t`Name`)} value={name} />
        <Detail
          css="display: flex; flex: 1;"
          value={<Sparkline jobs={host.summary_fields.recent_jobs} />}
          label={i18n._(t`Activity`)}
        />
        <Detail label={i18n._(t`Description`)} value={description} />
        {summary_fields.inventory && (
          <Detail
            label={i18n._(t`Inventory`)}
            value={
              <Link
                to={`/inventories/${
                  summary_fields.inventory.kind === 'smart'
                    ? 'smart_inventory'
                    : 'inventory'
                }/${summary_fields.inventory.id}/details`}
              >
                {summary_fields.inventory.name}
              </Link>
            }
          />
        )}
        <Detail label={i18n._(t`Created`)} value={createdBy} />
        <Detail label={i18n._(t`Last Modified`)} value={modifiedBy} />
        <VariablesDetail
          value={host.variables}
          rows={4}
          label={i18n._(t`Variables`)}
        />
      </DetailList>
      <CardActionsRow>
        {summary_fields.user_capabilities &&
          summary_fields.user_capabilities.edit && (
            <Button
              aria-label={i18n._(t`edit`)}
              component={Link}
              to={
                history.location.pathname.startsWith('/inventories')
                  ? `/inventories/inventory/${match.params.id}/hosts/${match.params.hostId}/edit`
                  : `/hosts/${id}/edit`
              }
            >
              {i18n._(t`Edit`)}
            </Button>
          )}
      </CardActionsRow>
    </CardBody>
  );
}

HostDetail.propTypes = {
  host: Host.isRequired,
};

export default withI18n()(HostDetail);
