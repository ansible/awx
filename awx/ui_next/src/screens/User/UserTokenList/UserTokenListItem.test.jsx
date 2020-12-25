import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import UserTokenListItem from './UserTokenListItem';

const token = {
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
      name: 'Foobar app',
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
};

describe('<UserTokenListItem />', () => {
  let wrapper;
  test('should mount properly', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<UserTokenListItem token={token} />);
    });
    expect(wrapper.find('UserTokenListItem').length).toBe(1);
  });

  test('should render application access token row properly', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <UserTokenListItem isSelected={false} token={token} />
      );
    });
    expect(wrapper.find('DataListCheck').prop('checked')).toBe(false);
    expect(wrapper.find('PFDataListCell[aria-label="Token type"]').text()).toBe(
      'Application access token'
    );
    expect(
      wrapper.find('PFDataListCell[aria-label="Application name"]').text()
    ).toContain('Foobar app');
    expect(wrapper.find('PFDataListCell[aria-label="Scope"]').text()).toContain(
      'Read'
    );
    expect(
      wrapper.find('PFDataListCell[aria-label="Expiration"]').text()
    ).toContain('10/25/3019, 3:06:43 PM');
  });

  test('should render personal access token row properly', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <UserTokenListItem
          isSelected={false}
          token={{
            ...token,
            refresh_token: null,
            application: null,
            scope: 'write',
            summary_fields: {
              user: token.summary_fields.user,
            },
          }}
        />
      );
    });
    expect(wrapper.find('DataListCheck').prop('checked')).toBe(false);
    expect(wrapper.find('PFDataListCell[aria-label="Token type"]').text()).toBe(
      'Personal access token'
    );
    expect(
      wrapper.find('PFDataListCell[aria-label="Application name"]').text()
    ).toBe('');
    expect(wrapper.find('PFDataListCell[aria-label="Scope"]').text()).toContain(
      'Write'
    );
    expect(
      wrapper.find('PFDataListCell[aria-label="Expiration"]').text()
    ).toContain('10/25/3019, 3:06:43 PM');
  });

  test('should be checked', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <UserTokenListItem isSelected token={token} />
      );
    });
    expect(wrapper.find('DataListCheck').prop('checked')).toBe(true);
  });
});
