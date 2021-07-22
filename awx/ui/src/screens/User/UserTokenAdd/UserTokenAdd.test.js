import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { UsersAPI, TokensAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import UserTokenAdd from './UserTokenAdd';

jest.mock('../../../api');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  history: () => ({
    location: '/user',
  }),
  useParams: () => ({ id: 1 }),
}));
let wrapper;

const onSuccessfulAdd = jest.fn();

describe('<UserTokenAdd />', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  test('handleSubmit should post to api', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <UserTokenAdd onSuccessfulAdd={onSuccessfulAdd} />
      );
    });
    UsersAPI.createToken.mockResolvedValueOnce({ data: { id: 1 } });
    const tokenData = {
      application: {
        id: 1,
      },
      description: 'foo',
      scope: 'read',
    };
    await act(async () => {
      wrapper.find('UserTokenForm').prop('handleSubmit')(tokenData);
    });
    expect(UsersAPI.createToken).toHaveBeenCalledWith(1, {
      application: 1,
      description: 'foo',
      scope: 'read',
    });
  });

  test('should navigate to tokens list when cancel is clicked', async () => {
    const history = createMemoryHistory({});
    await act(async () => {
      wrapper = mountWithContexts(
        <UserTokenAdd onSuccessfulAdd={onSuccessfulAdd} />,
        {
          context: { router: { history } },
        }
      );
    });
    await act(async () => {
      wrapper.find('button[aria-label="Cancel"]').prop('onClick')();
    });
    expect(history.location.pathname).toEqual('/users/1/tokens');
  });

  test('successful form submission with application', async () => {
    const history = createMemoryHistory({});
    const tokenData = {
      application: {
        id: 1,
      },
      description: 'foo',
      scope: 'read',
    };
    const rtnData = {
      id: 2,
      token: 'abc',
      refresh_token: 'def',
      expires: '3020-03-28T14:26:48.099297Z',
    };
    UsersAPI.createToken.mockResolvedValueOnce({
      data: rtnData,
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <UserTokenAdd onSuccessfulAdd={onSuccessfulAdd} />,
        {
          context: { router: { history } },
        }
      );
    });
    await waitForElement(wrapper, 'button[aria-label="Save"]');
    await act(async () => {
      wrapper.find('UserTokenForm').prop('handleSubmit')(tokenData);
    });
    expect(history.location.pathname).toEqual('/users/1/tokens/2/details');
    expect(onSuccessfulAdd).toHaveBeenCalledWith(rtnData);
  });

  test('successful form submission without application', async () => {
    const history = createMemoryHistory({});
    const tokenData = {
      scope: 'read',
    };
    const rtnData = {
      id: 2,
      token: 'abc',
      refresh_token: null,
      expires: '3020-03-28T14:26:48.099297Z',
    };
    TokensAPI.create.mockResolvedValueOnce({
      data: rtnData,
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <UserTokenAdd onSuccessfulAdd={onSuccessfulAdd} />,
        {
          context: { router: { history } },
        }
      );
    });
    await waitForElement(wrapper, 'button[aria-label="Save"]');
    await act(async () => {
      wrapper.find('UserTokenForm').prop('handleSubmit')(tokenData);
    });
    expect(history.location.pathname).toEqual('/users/1/tokens/2/details');
    expect(onSuccessfulAdd).toHaveBeenCalledWith(rtnData);
  });
});
