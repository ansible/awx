import React, { useCallback } from 'react';
import { Link, useHistory, useParams } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button } from '@patternfly/react-core';

import AlertModal from '../../../components/AlertModal';
import { CardBody, CardActionsRow } from '../../../components/Card';
import DeleteButton from '../../../components/DeleteButton';
import {
  DetailList,
  Detail,
  UserDateDetail,
} from '../../../components/DetailList';
import ErrorDetail from '../../../components/ErrorDetail';
import { TokensAPI } from '../../../api';
import useRequest, { useDismissableError } from '../../../util/useRequest';
import { toTitleCase } from '../../../util/strings';

function UserTokenDetail({ token, canEditOrDelete, i18n }) {
  const { scope, description, created, modified, summary_fields } = token;
  const history = useHistory();
  const { id, tokenId } = useParams();
  const { request: deleteToken, isLoading, error: deleteError } = useRequest(
    useCallback(async () => {
      await TokensAPI.destroy(tokenId);
      history.push(`/users/${id}/tokens`);
    }, [tokenId, id, history])
  );
  const { error, dismissError } = useDismissableError(deleteError);

  return (
    <CardBody>
      <DetailList>
        <Detail
          label={i18n._(t`Application`)}
          value={summary_fields?.application?.name}
          dataCy="application-token-detail-name"
        />
        <Detail label={i18n._(t`Description`)} value={description} />
        <Detail label={i18n._(t`Scope`)} value={toTitleCase(scope)} />
        <UserDateDetail
          label={i18n._(t`Created`)}
          date={created}
          user={summary_fields.user}
        />
        <UserDateDetail
          label={i18n._(t`Last Modified`)}
          date={modified}
          user={summary_fields.user}
        />
      </DetailList>
      <CardActionsRow>
        {canEditOrDelete && (
          <>
            <Button
              aria-label={i18n._(t`Edit`)}
              component={Link}
              to={`/users/${id}/tokens/${tokenId}/details`}
            >
              {i18n._(t`Edit`)}
            </Button>
            <DeleteButton
              name={summary_fields?.application?.name}
              modalTitle={i18n._(t`Delete User Token`)}
              onConfirm={deleteToken}
              isDisabled={isLoading}
            >
              {i18n._(t`Delete`)}
            </DeleteButton>
          </>
        )}
      </CardActionsRow>
      {error && (
        <AlertModal
          isOpen={error}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={dismissError}
        >
          {i18n._(t`Failed to user token.`)}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </CardBody>
  );
}

export default withI18n()(UserTokenDetail);
