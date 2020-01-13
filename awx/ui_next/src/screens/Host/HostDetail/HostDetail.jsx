import React, { useState } from 'react';
import { Link, useHistory, useParams, useLocation } from 'react-router-dom';
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

function HostDetail({ host, i18n, onUpdateHost }) {
  const {
    created,
    description,
    id,
    modified,
    name,
    enabled,
    summary_fields: {
      inventory,
      recent_jobs,
      kind,
      created_by,
      modified_by,
      user_capabilities,
    },
  } = host;

  const history = useHistory();
  const { pathname } = useLocation();
  const { id: inventoryId, hostId: inventoryHostId } = useParams();
  const [isLoading, setIsloading] = useState(false);
  const [deletionError, setDeletionError] = useState(false);
  const [toggleLoading, setToggleLoading] = useState(false);
  const [toggleError, setToggleError] = useState(false);

  const handleHostToggle = async () => {
    setToggleLoading(true);
    try {
      const { data } = await HostsAPI.update(id, {
        enabled: !enabled,
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
      await HostsAPI.destroy(id);
      setIsloading(false);
      history.push(`/inventories/inventory/${inventoryId}/hosts`);
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
        {i18n._(t`Failed to delete ${name}.`)}
        <ErrorDetail error={deletionError} />
      </AlertModal>
    );
  }
  return (
    <CardBody>
      <Switch
        css="padding-bottom: 40px"
        id={`host-${id}-toggle`}
        label={i18n._(t`On`)}
        labelOff={i18n._(t`Off`)}
        isChecked={enabled}
        isDisabled={!user_capabilities.edit}
        onChange={() => handleHostToggle()}
        aria-label={i18n._(t`Toggle Host`)}
      />
      <DetailList gutter="sm">
        <Detail label={i18n._(t`Name`)} value={name} />
        <Detail
          css="display: flex; flex: 1;"
          value={<Sparkline jobs={recent_jobs} />}
          label={i18n._(t`Activity`)}
        />
        <Detail label={i18n._(t`Description`)} value={description} />
        {inventory && (
          <Detail
            label={i18n._(t`Inventory`)}
            value={
              <Link
                to={`/inventories/${
                  kind === 'smart' ? 'smart_inventory' : 'inventory'
                }/${inventoryId}/details`}
              >
                {inventory.name}
              </Link>
            }
          />
        )}
        <UserDateDetail
          date={created}
          label={i18n._(t`Created`)}
          user={created_by}
        />
        <UserDateDetail
          label={i18n._(t`Last Modified`)}
          user={modified_by}
          date={modified}
        />
        <VariablesDetail
          value={host.variables}
          rows={4}
          label={i18n._(t`Variables`)}
        />
      </DetailList>
      <CardActionsRow>
        {user_capabilities && user_capabilities.edit && (
          <Button
            aria-label={i18n._(t`edit`)}
            component={Link}
            to={
              pathname.startsWith('/inventories')
                ? `/inventories/inventory/${inventoryId}/hosts/${inventoryHostId}/edit`
                : `/hosts/${id}/edit`
            }
          >
            {i18n._(t`Edit`)}
          </Button>
        )}
        {user_capabilities && user_capabilities.delete && (
          <DeleteButton
            onConfirm={() => handleHostDelete()}
            modalTitle={i18n._(t`Delete Host`)}
            name={host.name}
          />
        )}
      </CardActionsRow>
    </CardBody>
  );
}

HostDetail.propTypes = {
  host: Host.isRequired,
};

export default withI18n()(HostDetail);
