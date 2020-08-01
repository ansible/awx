import 'styled-components/macro';
import React, { useState } from 'react';
import { Link, useHistory } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button } from '@patternfly/react-core';
import { Host } from '../../../types';
import { CardBody, CardActionsRow } from '../../../components/Card';
import AlertModal from '../../../components/AlertModal';
import ErrorDetail from '../../../components/ErrorDetail';
import {
  DetailList,
  Detail,
  UserDateDetail,
} from '../../../components/DetailList';
import { VariablesDetail } from '../../../components/CodeMirrorInput';
import Sparkline from '../../../components/Sparkline';
import DeleteButton from '../../../components/DeleteButton';
import { HostsAPI } from '../../../api';
import HostToggle from '../../../components/HostToggle';

function InventoryHostDetail({ i18n, host }) {
  const {
    created,
    description,
    id,
    modified,
    name,
    variables,
    summary_fields: {
      inventory,
      recent_jobs,
      created_by,
      modified_by,
      user_capabilities,
    },
  } = host;

  const [isLoading, setIsloading] = useState(false);
  const [deletionError, setDeletionError] = useState(false);
  const history = useHistory();

  const handleHostDelete = async () => {
    setIsloading(true);
    try {
      await HostsAPI.destroy(id);
      history.push(`/inventories/inventory/${inventory.id}/hosts`);
    } catch (err) {
      setDeletionError(err);
    } finally {
      setIsloading(false);
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

  const recentPlaybookJobs = recent_jobs.map(job => ({ ...job, type: 'job' }));

  return (
    <CardBody>
      <HostToggle host={host} css="padding-bottom: 40px" />
      <DetailList gutter="sm">
        <Detail label={i18n._(t`Name`)} value={name} />
        {recentPlaybookJobs?.length > 0 && (
          <Detail
            label={i18n._(t`Activity`)}
            value={<Sparkline jobs={recentPlaybookJobs} />}
          />
        )}
        <Detail label={i18n._(t`Description`)} value={description} />
        <UserDateDetail
          date={created}
          label={i18n._(t`Created`)}
          user={created_by}
        />
        <UserDateDetail
          date={modified}
          label={i18n._(t`Last Modified`)}
          user={modified_by}
        />
        <VariablesDetail
          label={i18n._(t`Variables`)}
          rows={4}
          value={variables}
        />
      </DetailList>
      <CardActionsRow>
        {user_capabilities?.edit && (
          <Button
            aria-label={i18n._(t`edit`)}
            component={Link}
            to={`/inventories/inventory/${inventory.id}/hosts/${id}/edit`}
          >
            {i18n._(t`Edit`)}
          </Button>
        )}
        {user_capabilities?.delete && (
          <DeleteButton
            name={name}
            modalTitle={i18n._(t`Delete Host`)}
            onConfirm={() => handleHostDelete()}
          />
        )}
      </CardActionsRow>
      {deletionError && (
        <AlertModal
          isOpen={deletionError}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={() => setDeletionError(null)}
        >
          {i18n._(t`Failed to delete host.`)}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      )}
    </CardBody>
  );
}

InventoryHostDetail.propTypes = {
  host: Host.isRequired,
};

export default withI18n()(InventoryHostDetail);
