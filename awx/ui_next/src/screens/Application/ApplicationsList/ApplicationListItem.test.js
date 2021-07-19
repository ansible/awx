import React from 'react';
import { act } from 'react-dom/test-utils';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import ApplicationListItem from './ApplicationListItem';

describe('<ApplicationListItem/>', () => {
  let wrapper;
  const application = {
    id: 1,
    name: 'Foo',
    summary_fields: {
      organization: { id: 2, name: 'Organization' },
      user_capabilities: { edit: true },
    },
  };
  test('should mount successfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <table>
          <tbody>
            <ApplicationListItem
              application={application}
              detailUrl="/organizations/2/details"
              isSelected={false}
              onSelect={() => {}}
            />
          </tbody>
        </table>
      );
    });
    expect(wrapper.find('ApplicationListItem').length).toBe(1);
  });
  test('should render the proper data', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <table>
          <tbody>
            <ApplicationListItem
              application={application}
              detailUrl="/organizations/2/details"
              isSelected={false}
              onSelect={() => {}}
            />
          </tbody>
        </table>
      );
    });
    expect(
      wrapper
        .find('Td')
        .at(1)
        .text()
    ).toBe('Foo');
    expect(
      wrapper
        .find('Td')
        .at(2)
        .text()
    ).toBe('Organization');
    expect(wrapper.find('PencilAltIcon').length).toBe(1);
  });
});
