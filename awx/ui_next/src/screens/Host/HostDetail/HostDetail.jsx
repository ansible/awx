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
import Sparkline from '@components/Sparkline';
import DeleteButton from '@components/DeleteButton';
import { HostsAPI } from '@api';
import HostToggle from '@components/HostToggle';

function HostDetail({ host, i18n, onUpdateHost }) {
  const {
    created,
    description,
    id,
    modified,
    name,
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

  const recentPlaybookJobs = recent_jobs.map(job => ({ ...job, type: 'job' }));

  const handleHostDelete = async () => {
    setIsloading(true);
    try {
      await HostsAPI.destroy(id);
      setIsloading(false);
      const url = pathname.startsWith('/inventories')
        ? `/inventories/inventory/${inventoryId}/hosts/`
        : `/hosts`;
      history.push(url);
    } catch (err) {
      setDeletionError(err);
    }
  };

  if (!isLoading && deletionError) {
    return (
      <AlertModal
        isOpen={deletionError}
        variant="error"
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
      <HostToggle
        host={host}
        onToggle={enabled =>
          onUpdateHost({
            ...host,
            enabled,
          })
        }
        css="padding-bottom: 40px"
      />
      <DetailList gutter="sm">
        <Detail label={i18n._(t`Name`)} value={name} dataCy="host-name"/>
        <Detail
          value={<Sparkline jobs={recentPlaybookJobs} />}
          label={i18n._(t`Activity`)}
        />
        <Detail label={i18n._(t`Description`)} value={description}/>
        {inventory && (
          <Detail
            label={i18n._(t`Inventory`)}
            dataCy="host-inventory"
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
          dataCy="host-created-by"
        />
        <UserDateDetail
          label={i18n._(t`Last Modified`)}
          user={modified_by}
          date={modified}
          dataCy="host-last-modified-by"
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
