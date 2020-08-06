import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import { UsersAPI, TokensAPI } from '../../../api';
import UserTokenList from './UserTokenList';

jest.mock('../../../api/models/Users');
jest.mock('../../../api/models/Tokens');

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useLocation: () => ({
    search: '',
  }),
  useParams: () => ({
    id: 1,
  }),
}));

const tokens = {
  data: {
    results: [
      {
        id: 1,
        type: 'o_auth2_access_token',
        url: '/api/v2/tokens/1/',
        related: {
          user: '/api/v2/users/1/',
          application: '/api/v2/applications/1/',
          activity_stream: '/api/v2/tokens/1/activity_stream/',
        },
        summary_fields: {
          user: {
            id: 1,
            username: 'admin',
            first_name: '',
            last_name: '',
          },
          application: {
            id: 1,
            name: 'app',
          },
        },
        created: '2020-06-23T15:06:43.188634Z',
        modified: '2020-06-23T15:06:43.224151Z',
        description: '',
        user: 1,
        token: '************',
        refresh_token: '************',
        application: 1,
        expires: '3019-10-25T15:06:43.182788Z',
        scope: 'read',
      },
      {
        id: 2,
        type: 'o_auth2_access_token',
        url: '/api/v2/tokens/2/',
        related: {
          user: '/api/v2/users/1/',
          application: '/api/v2/applications/3/',
          activity_stream: '/api/v2/tokens/2/activity_stream/',
        },
        summary_fields: {
          user: {
            id: 1,
            username: 'admin',
            first_name: '',
            last_name: '',
          },
          application: {
            id: 3,
            name: 'hg',
          },
        },
        created: '2020-06-23T19:56:38.422053Z',
        modified: '2020-06-23T19:56:38.441353Z',
        description: 'cdfsg',
        user: 1,
        token: '************',
        refresh_token: '************',
        application: 3,
        expires: '3019-10-25T19:56:38.395635Z',
        scope: 'read',
      },
      {
        id: 3,
        type: 'o_auth2_access_token',
        url: '/api/v2/tokens/3/',
        related: {
          user: '/api/v2/users/1/',
          application: '/api/v2/applications/3/',
          activity_stream: '/api/v2/tokens/3/activity_stream/',
        },
        summary_fields: {
          user: {
            id: 1,
            username: 'admin',
            first_name: '',
            last_name: '',
          },
          application: {
            id: 3,
            name: 'hg',
          },
        },
        created: '2020-06-23T19:56:50.536169Z',
        modified: '2020-06-23T19:56:50.549521Z',
        description: 'fgds',
        user: 1,
        token: '************',
        refresh_token: '************',
        application: 3,
        expires: '3019-10-25T19:56:50.529306Z',
        scope: 'write',
      },
    ],
    count: 3,
  },
};

describe('<UserTokenList />', () => {
  let wrapper;

  beforeEach(() => {
    UsersAPI.readTokens.mockResolvedValue(tokens);
    UsersAPI.readTokenOptions.mockResolvedValue({
      data: { related_search_fields: [] },
    });
  });

  test('should mount properly, and fetch tokens', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<UserTokenList />);
    });
    expect(UsersAPI.readTokens).toHaveBeenCalledWith(1, {
      order_by: 'application__name',
      page: 1,
      page_size: 20,
    });
    expect(wrapper.find('UserTokenList').length).toBe(1);
  });

  test('edit button should be disabled', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<UserTokenList />);
    });
    waitForElement(wrapper, 'ContentEmpty', el => el.length === 0);
  });

  test('should enable edit button', async () => {
    UsersAPI.readTokens.mockResolvedValue(tokens);
    await act(async () => {
      wrapper = mountWithContexts(<UserTokenList />);
    });
    waitForElement(wrapper, 'ContentEmpty', el => el.length === 0);
    expect(
      wrapper.find('DataListCheck[id="select-token-3"]').props().checked
    ).toBe(false);
    await act(async () => {
      wrapper.find('DataListCheck[id="select-token-3"]').invoke('onChange')(
        true
      );
    });
    wrapper.update();
    expect(
      wrapper.find('DataListCheck[id="select-token-3"]').props().checked
    ).toBe(true);
  });
  test('delete button should be disabled', async () => {
    UsersAPI.readTokens.mockResolvedValue(tokens);
    await act(async () => {
      wrapper = mountWithContexts(<UserTokenList />);
    });
    waitForElement(wrapper, 'ContentEmpty', el => el.length === 0);
    expect(wrapper.find('Button[aria-label="Delete"]').prop('isDisabled')).toBe(
      true
    );
  });
  test('should select and then delete item properly', async () => {
    UsersAPI.readTokens.mockResolvedValue(tokens);
    await act(async () => {
      wrapper = mountWithContexts(<UserTokenList />);
    });
    waitForElement(wrapper, 'ContentEmpty', el => el.length === 0);
    expect(wrapper.find('Button[aria-label="Delete"]').prop('isDisabled')).toBe(
      true
    );
    await act(async () => {
      wrapper
        .find('DataListCheck[aria-labelledby="check-action-3"]')
        .prop('onChange')(tokens.data.results[0]);
    });
    wrapper.update();
    expect(
      wrapper
        .find('DataListCheck[aria-labelledby="check-action-3"]')
        .prop('checked')
    ).toBe(true);
    expect(wrapper.find('Button[aria-label="Delete"]').prop('isDisabled')).toBe(
      false
    );
    await act(async () =>
      wrapper.find('Button[aria-label="Delete"]').prop('onClick')()
    );
    wrapper.update();
    await act(async () => expect(wrapper.find('AlertModal').length).toBe(1));
    await act(async () =>
      wrapper.find('Button[aria-label="confirm delete"]').prop('onClick')()
    );
    wrapper.update();
    expect(TokensAPI.destroy).toHaveBeenCalledWith(3);
  });
  test('should select and then delete item properly', async () => {
    UsersAPI.readTokens.mockResolvedValue(tokens);
    TokensAPI.destroy.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'delete',
            url: '/api/v2/tokens',
          },
          data: 'An error occurred',
          status: 403,
        },
      })
    );
    await act(async () => {
      wrapper = mountWithContexts(<UserTokenList />);
    });
    waitForElement(wrapper, 'ContentEmpty', el => el.length === 0);
    expect(wrapper.find('Button[aria-label="Delete"]').prop('isDisabled')).toBe(
      true
    );
    await act(async () => {
      wrapper
        .find('DataListCheck[aria-labelledby="check-action-3"]')
        .prop('onChange')(tokens.data.results[0]);
    });
    wrapper.update();
    expect(
      wrapper
        .find('DataListCheck[aria-labelledby="check-action-3"]')
        .prop('checked')
    ).toBe(true);
    expect(wrapper.find('Button[aria-label="Delete"]').prop('isDisabled')).toBe(
      false
    );
    await act(async () =>
      wrapper.find('Button[aria-label="Delete"]').prop('onClick')()
    );
    wrapper.update();
    await act(async () => expect(wrapper.find('AlertModal').length).toBe(1));
    await act(async () =>
      wrapper.find('Button[aria-label="confirm delete"]').prop('onClick')()
    );
    wrapper.update();
    expect(TokensAPI.destroy).toHaveBeenCalledWith(3);
    wrapper.update();
    expect(wrapper.find('ErrorDetail').length).toBe(1);
  });
});
