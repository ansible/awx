import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import UserTokenAdd from './UserTokenAdd';
import { UsersAPI, TokensAPI } from '../../../api';

jest.mock('../../../api');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  history: () => ({
    location: '/user',
  }),
  useParams: () => ({ id: 1 }),
}));
let wrapper;

describe('<UserTokenAdd />', () => {
  test('handleSubmit should post to api', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<UserTokenAdd />);
    });
    UsersAPI.createToken.mockResolvedValueOnce({ data: { id: 1 } });
    const tokenData = {
      application: 1,
      description: 'foo',
      scope: 'read',
    };
    await act(async () => {
      wrapper.find('UserTokenForm').prop('handleSubmit')(tokenData);
    });
    expect(UsersAPI.createToken).toHaveBeenCalledWith(1, tokenData);
  });

  test('should navigate to tokens list when cancel is clicked', async () => {
    const history = createMemoryHistory({});
    await act(async () => {
      wrapper = mountWithContexts(<UserTokenAdd />, {
        context: { router: { history } },
      });
    });
    await act(async () => {
      wrapper.find('button[aria-label="Cancel"]').prop('onClick')();
    });
    expect(history.location.pathname).toEqual('/users/1/tokens');
  });

  test('successful form submission should trigger redirect', async () => {
    const history = createMemoryHistory({});
    const tokenData = {
      application: 1,
      description: 'foo',
      scope: 'read',
    };
    UsersAPI.createToken.mockResolvedValueOnce({
      data: {
        id: 2,
        ...tokenData,
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(<UserTokenAdd />, {
        context: { router: { history } },
      });
    });
    await waitForElement(wrapper, 'button[aria-label="Save"]');
    await act(async () => {
      wrapper.find('UserTokenForm').prop('handleSubmit')(tokenData);
    });
    expect(history.location.pathname).toEqual('/users/1/tokens');
  });

  test('should successful submit form with application', async () => {
    const history = createMemoryHistory({});
    const tokenData = {
      scope: 'read',
    };
    TokensAPI.create.mockResolvedValueOnce({
      data: {
        id: 2,
        ...tokenData,
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(<UserTokenAdd />, {
        context: { router: { history } },
      });
    });
    await waitForElement(wrapper, 'button[aria-label="Save"]');
    await act(async () => {
      wrapper.find('UserTokenForm').prop('handleSubmit')(tokenData);
    });
    expect(history.location.pathname).toEqual('/users/1/tokens');
  });
});
