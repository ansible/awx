import React from 'react';
import { act } from 'react-dom/test-utils';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import CredentialTypeListItem from './CredentialTypeListItem';

describe('<CredentialTypeListItem/>', () => {
  let wrapper;
  const credential_type = {
    id: 1,
    name: 'Foo',
    summary_fields: { user_capabilities: { edit: true, delete: true } },
    kind: 'cloud',
  };

  test('should mount successfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <table>
          <tbody>
            <CredentialTypeListItem
              credentialType={credential_type}
              detailUrl="credential_types/1/details"
              isSelected={false}
              onSelect={() => {}}
            />
          </tbody>
        </table>
      );
    });
    expect(wrapper.find('CredentialTypeListItem').length).toBe(1);
  });

  test('should render the proper data', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <table>
          <tbody>
            <CredentialTypeListItem
              credentialType={credential_type}
              detailsUrl="credential_types/1/details"
              isSelected={false}
              onSelect={() => {}}
            />
          </tbody>
        </table>
      );
    });
    expect(wrapper.find('Td[dataLabel="Name"]').text()).toBe('Foo');
    expect(wrapper.find('PencilAltIcon').length).toBe(1);
    expect(wrapper.find('.pf-c-table__check input').prop('checked')).toBe(
      undefined
    );
  });

  test('edit button shown to users with edit capabilities', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <table>
          <tbody>
            <CredentialTypeListItem
              credentialType={credential_type}
              detailsUrl="credential_types/1/details"
              isSelected
              onSelect={() => {}}
            />
          </tbody>
        </table>
      );
    });

    expect(wrapper.find('PencilAltIcon').exists()).toBeTruthy();
  });

  test('edit button hidden from users without edit capabilities', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <table>
          <tbody>
            <CredentialTypeListItem
              credentialType={{
                ...credential_type,
                summary_fields: { user_capabilities: { edit: false } },
              }}
              detailsUrl="credential_types/1/details"
              isSelected
              onSelect={() => {}}
            />
          </tbody>
        </table>
      );
    });

    expect(wrapper.find('PencilAltIcon').exists()).toBeFalsy();
  });
});
