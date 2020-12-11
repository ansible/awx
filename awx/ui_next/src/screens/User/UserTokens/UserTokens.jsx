import React, { useCallback, useState } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import { Switch, Route, useParams } from 'react-router-dom';
import {
  Alert,
  ClipboardCopy,
  ClipboardCopyVariant,
  Modal,
} from '@patternfly/react-core';
import { formatDateString } from '../../../util/dates';
import { Detail, DetailList } from '../../../components/DetailList';
import UserTokenAdd from '../UserTokenAdd';
import UserTokenList from '../UserTokenList';
import UserToken from '../UserToken';

const TokenAlert = styled(Alert)`
  margin-bottom: 20px;
`;

function UserTokens({ i18n, setBreadcrumb, user }) {
  const [tokenModalSource, setTokenModalSource] = useState(null);
  const { id } = useParams();

  const onSuccessfulAdd = useCallback(token => setTokenModalSource(token), [
    setTokenModalSource,
  ]);

  return (
    <>
      <Switch>
        <Route key="add" path="/users/:id/tokens/add">
          <UserTokenAdd id={Number(id)} onSuccessfulAdd={onSuccessfulAdd} />
        </Route>
        <Route key="token" path="/users/:id/tokens/:tokenId">
          <UserToken
            user={user}
            setBreadcrumb={setBreadcrumb}
            id={Number(id)}
          />
        </Route>
        <Route key="list" path="/users/:id/tokens">
          <UserTokenList id={Number(id)} />
        </Route>
      </Switch>
      {tokenModalSource && (
        <Modal
          aria-label={i18n._(t`Token information`)}
          isOpen
          variant="medium"
          title={i18n._(t`Token information`)}
          onClose={() => setTokenModalSource(null)}
        >
          <TokenAlert
            variant="info"
            isInline
            title={i18n._(
              t`This is the only time the token value and associated refresh token value will be shown.`
            )}
          />
          <DetailList stacked>
            {tokenModalSource.token && (
              <Detail
                label={i18n._(t`Token`)}
                value={
                  <ClipboardCopy
                    isReadOnly
                    variant={ClipboardCopyVariant.expansion}
                  >
                    {tokenModalSource.token}
                  </ClipboardCopy>
                }
              />
            )}
            {tokenModalSource.refresh_token && (
              <Detail
                label={i18n._(t`Refresh Token`)}
                value={
                  <ClipboardCopy
                    isReadOnly
                    variant={ClipboardCopyVariant.expansion}
                  >
                    {tokenModalSource.refresh_token}
                  </ClipboardCopy>
                }
              />
            )}
            <Detail
              label={i18n._(t`Expires`)}
              value={formatDateString(tokenModalSource.expires)}
            />
          </DetailList>
        </Modal>
      )}
    </>
  );
}

export default withI18n()(UserTokens);
