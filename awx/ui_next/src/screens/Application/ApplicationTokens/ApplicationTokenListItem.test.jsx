import React from 'react';
import { act } from 'react-dom/test-utils';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import ApplicationTokenListItem from './ApplicationTokenListItem';

describe('<ApplicationTokenListItem/>', () => {
  let wrapper;
  const token = {
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
  };

  test('should mount successfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ApplicationTokenListItem
          token={token}
          detailUrl="/users/2/details"
          isSelected={false}
          onSelect={() => {}}
        />
      );
    });
    expect(wrapper.find('ApplicationTokenListItem').length).toBe(1);
  });
  test('should render the proper data', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ApplicationTokenListItem
          token={token}
          detailUrl="/users/2/details"
          isSelected={false}
          onSelect={() => {}}
        />
      );
    });
    expect(wrapper.find('DataListCell[aria-label="token name"]').text()).toBe(
      'admin'
    );
    expect(wrapper.find('DataListCell[aria-label="scope"]').text()).toBe(
      'ScopeRead'
    );
    expect(wrapper.find('DataListCell[aria-label="expiration"]').text()).toBe(
      'Expiration10/25/3019, 7:56:38 PM'
    );
    expect(wrapper.find('input#select-token-2').prop('checked')).toBe(false);
  });
  test('should be checked', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ApplicationTokenListItem
          token={token}
          detailUrl="/users/2/details"
          isSelected
          onSelect={() => {}}
        />
      );
    });
    expect(wrapper.find('input#select-token-2').prop('checked')).toBe(true);
  });
});
