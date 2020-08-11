import React, { useCallback, useEffect } from 'react';
import { Link, useHistory } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { shape } from 'prop-types';
import { Button, Chip, Label } from '@patternfly/react-core';

import { Inventory } from '../../../types';
import { InventoriesAPI, UnifiedJobsAPI } from '../../../api';
import useRequest, { useDismissableError } from '../../../util/useRequest';

import AlertModal from '../../../components/AlertModal';
import { CardBody, CardActionsRow } from '../../../components/Card';
import ChipGroup from '../../../components/ChipGroup';
import { VariablesDetail } from '../../../components/CodeMirrorInput';
import ContentError from '../../../components/ContentError';
import ContentLoading from '../../../components/ContentLoading';
import DeleteButton from '../../../components/DeleteButton';
import {
  DetailList,
  Detail,
  UserDateDetail,
} from '../../../components/DetailList';
import ErrorDetail from '../../../components/ErrorDetail';
import Sparkline from '../../../components/Sparkline';

function SmartInventoryDetail({ inventory, i18n }) {
  const history = useHistory();
  const {
    created,
    description,
    host_filter,
    id,
    modified,
    name,
    variables,
    summary_fields: {
      created_by,
      modified_by,
      organization,
      user_capabilities,
    },
  } = inventory;

  const {
    error: contentError,
    isLoading: hasContentLoading,
    request: fetchData,
    result: { recentJobs, instanceGroups },
  } = useRequest(
    useCallback(async () => {
      const params = {
        or__job__inventory: id,
        or__workflowjob__inventory: id,
        order_by: '-finished',
        page_size: 10,
      };
      const [{ data: jobData }, { data: igData }] = await Promise.all([
        UnifiedJobsAPI.read(params),
        InventoriesAPI.readInstanceGroups(id),
      ]);
      return {
        recentJobs: jobData.results,
        instanceGroups: igData.results,
      };
    }, [id]),
    {
      recentJobs: [],
      instanceGroups: [],
    }
  );

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const { error: deleteError, isLoading, request: handleDelete } = useRequest(
    useCallback(async () => {
      await InventoriesAPI.destroy(id);
      history.push(`/inventories`);
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
    <>
      <CardBody>
        <DetailList>
          <Detail label={i18n._(t`Name`)} value={name} />
          {recentJobs.length > 0 && (
            <Detail
              label={i18n._(t`Activity`)}
              value={<Sparkline jobs={recentJobs} />}
            />
          )}
          <Detail label={i18n._(t`Description`)} value={description} />
          <Detail label={i18n._(t`Type`)} value={i18n._(t`Smart inventory`)} />
          <Detail
            label={i18n._(t`Organization`)}
            value={
              <Link to={`/organizations/${organization.id}/details`}>
                {organization.name}
              </Link>
            }
          />
          <Detail
            fullWidth
            label={i18n._(t`Smart host filter`)}
            value={<Label variant="outline">{host_filter}</Label>}
          />
          {instanceGroups.length > 0 && (
            <Detail
              fullWidth
              label={i18n._(t`Instance groups`)}
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
          <VariablesDetail
            label={i18n._(t`Variables`)}
            value={variables}
            rows={4}
          />
          <UserDateDetail
            label={i18n._(t`Created`)}
            date={created}
            user={created_by}
          />
          <UserDateDetail
            label={i18n._(t`Last modified`)}
            date={modified}
            user={modified_by}
          />
        </DetailList>
        <CardActionsRow>
          {user_capabilities?.edit && (
            <Button
              component={Link}
              aria-label="edit"
              to={`/inventories/smart_inventory/${id}/edit`}
            >
              {i18n._(t`Edit`)}
            </Button>
          )}
          {user_capabilities?.delete && (
            <DeleteButton
              name={name}
              modalTitle={i18n._(t`Delete smart inventory`)}
              onConfirm={handleDelete}
              isDisabled={isLoading}
            >
              {i18n._(t`Delete`)}
            </DeleteButton>
          )}
        </CardActionsRow>
      </CardBody>
      {error && (
        <AlertModal
          isOpen={error}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={dismissError}
        >
          {i18n._(t`Failed to delete smart inventory.`)}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </>
  );
}

SmartInventoryDetail.propTypes = {
  inventory: Inventory.isRequired,
  i18n: shape({}).isRequired,
};

export default withI18n()(SmartInventoryDetail);
