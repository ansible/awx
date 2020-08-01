import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import UserOrganizationListItem from './UserOrganizationListItem';

describe('<UserOrganizationListItem />', () => {
  test('mounts correctly', () => {
    let wrapper;
    act(() => {
      wrapper = mountWithContexts(
        <UserOrganizationListItem
          organization={{ name: 'foo', id: 1, description: 'Bar' }}
        />
      );
    });
    expect(wrapper.find('UserOrganizationListItem').length).toBe(1);
  });
  test('render correct information', () => {
    let wrapper;
    act(() => {
      wrapper = mountWithContexts(
        <UserOrganizationListItem
          organization={{ name: 'foo', id: 1, description: 'Bar' }}
        />
      );
    });
    expect(
      wrapper
        .find('DataListCell')
        .at(0)
        .text()
    ).toBe('foo');
    expect(
      wrapper
        .find('DataListCell')
        .at(1)
        .text()
    ).toBe('Bar');
    expect(wrapper.find('Link').prop('to')).toBe('/organizations/1/details');
  });
});
