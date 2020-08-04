import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { TokensAPI } from '../../../api';
import UserTokenDetail from './UserTokenDetail';

jest.mock('../../../api/models/Tokens');

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({
    id: 1,
    tokenId: 2,
  }),
}));
describe('<UserTokenDetail/>', () => {
  let wrapper;
  const token = {
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
  };
  test('should call api for token details and actions', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <UserTokenDetail canEditOrDelete token={token} />
      );
    });
    expect(wrapper.find('UserTokenDetail').length).toBe(1);
  });
  test('should call api for token details and actions', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <UserTokenDetail canEditOrDelete token={token} />
      );
    });

    expect(wrapper.find('Detail[label="Application"]').prop('value')).toBe(
      'hg'
    );
    expect(wrapper.find('Detail[label="Description"]').prop('value')).toBe(
      'cdfsg'
    );
    expect(wrapper.find('Detail[label="Scope"]').prop('value')).toBe('Read');
    expect(wrapper.find('UserDateDetail[label="Created"]').prop('date')).toBe(
      '2020-06-23T19:56:38.422053Z'
    );
    expect(
      wrapper.find('UserDateDetail[label="Last Modified"]').prop('date')
    ).toBe('2020-06-23T19:56:38.441353Z');
    expect(wrapper.find('Button[aria-label="Edit"]').length).toBe(1);
    expect(wrapper.find('Button[aria-label="Delete"]').length).toBe(1);
  });
  test('should not render edit or delete buttons', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <UserTokenDetail canEditOrDelete={false} token={token} />
      );
    });
    expect(wrapper.find('Button[aria-label="Edit"]').length).toBe(0);
    expect(wrapper.find('Button[aria-label="Delete"]').length).toBe(0);
  });
  test('should delete token properly', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <UserTokenDetail canEditOrDelete token={token} />
      );
    });
    await act(async () =>
      wrapper.find('Button[aria-label="Delete"]').prop('onClick')()
    );
    wrapper.update();
    await act(async () => wrapper.find('DeleteButton').prop('onConfirm')());
    expect(TokensAPI.destroy).toBeCalledWith(2);
  });
  test('should throw deletion error', async () => {
    TokensAPI.destroy.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'delete',
            url: '/api/v2/tokens',
          },
          data: 'An error occurred',
          status: 400,
        },
      })
    );
    await act(async () => {
      wrapper = mountWithContexts(
        <UserTokenDetail canEditOrDelete token={token} />
      );
    });
    await act(async () =>
      wrapper.find('Button[aria-label="Delete"]').prop('onClick')()
    );
    wrapper.update();
    await act(async () => wrapper.find('DeleteButton').prop('onConfirm')());
    expect(TokensAPI.destroy).toBeCalledWith(2);
    wrapper.update();
    expect(wrapper.find('ErrorDetail').length).toBe(1);
  });
});
