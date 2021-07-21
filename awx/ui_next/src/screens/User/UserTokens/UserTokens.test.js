import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import UserTokens from './UserTokens';

jest.mock('../../../api');

describe('<UserTokens />', () => {
  let wrapper;

  test('shows Application information modal after successful creation', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/users/1/tokens/add'],
    });
    wrapper = mountWithContexts(<UserTokens />, {
      context: { router: { history } },
    });
    expect(wrapper.find('Modal[title="Token information"]').length).toBe(0);
    await act(async () => {
      wrapper.find('UserTokenAdd').props().onSuccessfulAdd({
        expires: '3020-03-28T14:26:48.099297Z',
        token: 'foobar',
        refresh_token: 'aaaaaaaaaaaaaaaaaaaaaaaaaa',
      });
    });
    wrapper.update();
    expect(wrapper.find('Modal[title="Token information"]').length).toBe(1);
  });
});
