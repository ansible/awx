import React from 'react';
import { withI18n } from '@lingui/react';
import { Switch, Route, useParams } from 'react-router-dom';
import UserTokenAdd from '../UserTokenAdd';
import UserTokenList from '../UserTokenList';
import UserToken from '../UserToken';

function UserTokens({ setBreadcrumb, user }) {
  const { id } = useParams();
  return (
    <Switch>
      <Route key="add" path="/users/:id/tokens/add">
        <UserTokenAdd id={Number(id)} />
      </Route>
      <Route key="token" path="/users/:id/tokens/:tokenId">
        <UserToken user={user} setBreadcrumb={setBreadcrumb} id={Number(id)} />
      </Route>
      <Route key="list" path="/users/:id/tokens">
        <UserTokenList id={Number(id)} />
      </Route>
    </Switch>
  );
}

export default withI18n()(UserTokens);
