import React, { useState } from 'react';
import { Link, withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Host } from '@types';
import { Button } from '@patternfly/react-core';
import { CardBody, CardActionsRow } from '@components/Card';
import AlertModal from '@components/AlertModal';
import ErrorDetail from '@components/ErrorDetail';
import { DetailList, Detail, UserDateDetail } from '@components/DetailList';
import { VariablesDetail } from '@components/CodeMirrorInput';
import { Sparkline } from '@components/Sparkline';
import DeleteButton from '@components/DeleteButton';
import Switch from '@components/Switch';
import { HostsAPI } from '@api';

function HostDetail({ host, i18n }) {
const ActionButtonWrapper = styled.div`
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
  & > :not(:first-child) {
    margin-left: 20px;
  }
`;

function HostDetail({ host, history, match, i18n, onUpdateHost }) {
  const { created, description, id, modified, name, summary_fields } = host;

  const [isLoading, setIsloading] = useState(false);
  const [deletionError, setDeletionError] = useState(false);
  const [toggleLoading, setToggleLoading] = useState(false);
  const [toggleError, setToggleError] = useState(false);

  const handleHostToggle = async () => {
    setToggleLoading(true);
    try {
      const { data } = await HostsAPI.update(host.id, {
        enabled: !host.enabled,
      });
      onUpdateHost(data);
    } catch (err) {
      setToggleError(err);
    } finally {
      setToggleLoading(false);
    }
  };

  const handleHostDelete = async () => {
    setIsloading(true);
    try {
      await HostsAPI.destroy(host.id);
      setIsloading(false);
      history.push(`/inventories/inventory/${match.params.id}/hosts`);
    } catch (err) {
      setDeletionError(err);
    }
  };

  if (toggleError && !toggleLoading) {
    return (
      <AlertModal
        variant="danger"
        title={i18n._(t`Error!`)}
        isOpen={toggleError && !toggleLoading}
        onClose={() => setToggleError(false)}
      >
        {i18n._(t`Failed to toggle host.`)}
        <ErrorDetail error={toggleError} />
      </AlertModal>
    );
  }
  if (!isLoading && deletionError) {
    return (
      <AlertModal
        isOpen={deletionError}
        variant="danger"
        title={i18n._(t`Error!`)}
        onClose={() => setDeletionError(false)}
      >
        {i18n._(t`Failed to delete ${host.name}.`)}
        <ErrorDetail error={deletionError} />
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
        onChange={() => handleHostToggle()}
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
        <UserDateDetail
          date={created}
          label={i18n._(t`Created`)}
          user={summary_fields.created_by}
        />
        <UserDateDetail
          label={i18n._(t`Last Modified`)}
          user={summary_fields.modified_by}
          date={modified}
        />
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
        {summary_fields.user_capabilities &&
          summary_fields.user_capabilities.delete && (
            <DeleteButton
              onConfirm={() => handleHostDelete()}
              modalTitle={i18n._(t`Delete Host`)}
              name={host.name}
            />
          )}
    </CardBody>
  );
}

HostDetail.propTypes = {
  host: Host.isRequired,
};

export default withI18n()(HostDetail);
