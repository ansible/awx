import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import UserOrganizationListItem from './UserOrganizationListItem';

describe('<UserOrganizationListItem />', () => {
  test('mounts correctly', () => {
    let wrapper;
    act(() => {
      wrapper = mountWithContexts(
        <table>
          <tbody>
            <UserOrganizationListItem
              organization={{ name: 'foo', id: 1, description: 'Bar' }}
            />
          </tbody>
        </table>
      );
    });
    expect(wrapper.find('UserOrganizationListItem').length).toBe(1);
  });
  test('render correct information', () => {
    let wrapper;
    act(() => {
      wrapper = mountWithContexts(
        <table>
          <tbody>
            <UserOrganizationListItem
              organization={{ name: 'foo', id: 1, description: 'Bar' }}
            />
          </tbody>
        </table>
      );
    });
    expect(wrapper.find('Td').at(0).text()).toBe('foo');
    expect(wrapper.find('Td').at(1).text()).toBe('Bar');
    expect(wrapper.find('Link').prop('to')).toBe('/organizations/1/details');
  });
});
