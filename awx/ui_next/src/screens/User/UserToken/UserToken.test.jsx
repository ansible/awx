import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { TokensAPI } from '../../../api';
import UserToken from './UserToken';

jest.mock('../../../api/models/Tokens');

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({
    id: 1,
    tokenId: 2,
  }),
}));
describe('<UserToken/>', () => {
  let wrapper;
  const user = {
    id: 1,
    type: 'user',
    url: '/api/v2/users/1/',
    summary_fields: {
      user_capabilities: {
        edit: true,
        delete: false,
      },
    },
    created: '2020-06-19T12:55:13.138692Z',
    username: 'admin',
    first_name: 'Alex',
    last_name: 'Corey',
    email: 'a@g.com',
  };
  test('should call api for token details and actions', async () => {
    TokensAPI.readDetail.mockResolvedValue({
      id: 2,
      type: 'o_auth2_access_token',
      url: '/api/v2/tokens/2/',

      summary_fields: {
        user: {
          id: 1,
          username: 'admin',
          first_name: 'Alex',
          last_name: 'Corey',
        },
        application: {
          id: 3,
          name: 'hg',
        },
      },
      created: '2020-06-23T19:56:38.422053Z',
      modified: '2020-06-23T19:56:38.441353Z',
      description: 'cdfsg',
      scope: 'read',
    });
    TokensAPI.readOptions.mockResolvedValue({
      data: { actions: { POST: true } },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <UserToken setBreadcrumb={jest.fn()} user={user} />
      );
    });
    expect(wrapper.find('UserToken').length).toBe(1);
  });
  test('should call api for token details and actions', async () => {
    TokensAPI.readDetail.mockResolvedValue({
      id: 2,
      type: 'o_auth2_access_token',
      url: '/api/v2/tokens/2/',

      summary_fields: {
        user: {
          id: 1,
          username: 'admin',
          first_name: 'Alex',
          last_name: 'Corey',
        },
        application: {
          id: 3,
          name: 'hg',
        },
      },
      created: '2020-06-23T19:56:38.422053Z',
      modified: '2020-06-23T19:56:38.441353Z',
      description: 'cdfsg',
      scope: 'read',
    });
    TokensAPI.readOptions.mockResolvedValue({
      data: { actions: { POST: true } },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <UserToken setBreadcrumb={jest.fn()} user={user} />
      );
    });
    expect(TokensAPI.readDetail).toBeCalledWith(2);
    expect(TokensAPI.readOptions).toBeCalled();
  });
});
