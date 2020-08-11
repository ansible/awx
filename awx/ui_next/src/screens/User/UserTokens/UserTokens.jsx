import React from 'react';
import { withI18n } from '@lingui/react';
import { Switch, Route, useParams } from 'react-router-dom';
import UserTokenAdd from '../UserTokenAdd';
import UserTokenList from '../UserTokenList';

function UserTokens() {
  const { id: userId } = useParams();

  return (
    <Switch>
      <Route key="add" path="/users/:id/tokens/add">
        <UserTokenAdd id={Number(userId)} />
      </Route>
      <Route key="list" path="/users/:id/tokens">
        <UserTokenList id={Number(userId)} />
      </Route>
    </Switch>
  );
}

export default withI18n()(UserTokens);
