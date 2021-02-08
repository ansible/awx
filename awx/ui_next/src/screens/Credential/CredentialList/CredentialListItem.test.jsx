import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { CredentialListItem } from '.';
import { mockCredentials } from '../shared';
import { CredentialsAPI } from '../../../api';

jest.mock('../../../api');

describe('<CredentialListItem />', () => {
  let wrapper;

  afterEach(() => {
    wrapper.unmount();
  });

  test('edit button shown to users with edit capabilities', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <CredentialListItem
            credential={mockCredentials.results[0]}
            detailUrl="/foo/bar"
            isSelected={false}
            onSelect={() => {}}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('PencilAltIcon').exists()).toBeTruthy();
  });

  test('edit button hidden from users without edit capabilities', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <CredentialListItem
            credential={mockCredentials.results[1]}
            detailUrl="/foo/bar"
            isSelected={false}
            onSelect={() => {}}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('PencilAltIcon').exists()).toBeFalsy();
  });
  test('should call api to copy template', async () => {
    CredentialsAPI.copy.mockResolvedValue();

    wrapper = mountWithContexts(
      <table>
        <tbody>
          <CredentialListItem
            isSelected={false}
            detailUrl="/foo/bar"
            credential={mockCredentials.results[0]}
            onSelect={() => {}}
          />
        </tbody>
      </table>
    );

    await act(async () =>
      wrapper.find('Button[aria-label="Copy"]').prop('onClick')()
    );
    expect(CredentialsAPI.copy).toHaveBeenCalled();
    jest.clearAllMocks();
  });

  test('should render proper alert modal on copy error', async () => {
    CredentialsAPI.copy.mockRejectedValue(new Error());

    wrapper = mountWithContexts(
      <table>
        <tbody>
          <CredentialListItem
            isSelected={false}
            detailUrl="/foo/bar"
            onSelect={() => {}}
            credential={mockCredentials.results[0]}
          />
        </tbody>
      </table>
    );
    await act(async () =>
      wrapper.find('Button[aria-label="Copy"]').prop('onClick')()
    );
    wrapper.update();
    expect(wrapper.find('Modal').prop('isOpen')).toBe(true);
    jest.clearAllMocks();
  });

  test('should not render copy button', async () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <CredentialListItem
            isSelected={false}
            detailUrl="/foo/bar"
            onSelect={() => {}}
            credential={mockCredentials.results[1]}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('CopyButton').length).toBe(0);
  });
});
