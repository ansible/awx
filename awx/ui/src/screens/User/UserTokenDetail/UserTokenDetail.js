import React, { useCallback } from 'react';
import { useHistory, useParams } from 'react-router-dom';

import { t } from '@lingui/macro';

import AlertModal from 'components/AlertModal';
import { CardBody, CardActionsRow } from 'components/Card';
import DeleteButton from 'components/DeleteButton';
import { DetailList, Detail, UserDateDetail } from 'components/DetailList';
import ErrorDetail from 'components/ErrorDetail';
import { TokensAPI } from 'api';
import { formatDateString } from 'util/dates';
import useRequest, { useDismissableError } from 'hooks/useRequest';
import { toTitleCase } from 'util/strings';
import helptext from '../shared/User.helptext';

function UserTokenDetail({ token }) {
  const { scope, description, created, modified, expires, summary_fields } =
    token;
  const history = useHistory();
  const { id, tokenId } = useParams();
  const {
    request: deleteToken,
    isLoading,
    error: deleteError,
  } = useRequest(
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
          label={t`Application`}
          value={summary_fields?.application?.name}
          dataCy="application-token-detail-name"
          helpText={helptext.application}
        />
        <Detail
          label={t`Description`}
          value={description}
          dataCy="application-token-detail-description"
        />
        <Detail
          label={t`Scope`}
          value={toTitleCase(scope)}
          dataCy="application-token-detail-scope"
          helpText={helptext.scope}
        />
        <Detail
          label={t`Expires`}
          value={formatDateString(expires)}
          dataCy="application-token-detail-expires"
        />
        <UserDateDetail
          label={t`Created`}
          date={created}
          user={summary_fields.user}
        />
        <UserDateDetail
          label={t`Last Modified`}
          date={modified}
          user={summary_fields.user}
        />
      </DetailList>
      <CardActionsRow>
        <DeleteButton
          name={summary_fields?.application?.name || t`Personal Access Token`}
          modalTitle={t`Delete User Token`}
          onConfirm={deleteToken}
          isDisabled={isLoading}
        >
          {t`Delete`}
        </DeleteButton>
      </CardActionsRow>
      {error && (
        <AlertModal
          isOpen={error}
          variant="error"
          title={t`Error!`}
          onClose={dismissError}
        >
          {t`Failed to user token.`}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </CardBody>
  );
}

export default UserTokenDetail;
