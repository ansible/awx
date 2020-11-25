import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import InventorySourceForm from './InventorySourceForm';
import { InventorySourcesAPI, ProjectsAPI, CredentialsAPI } from '../../../api';

jest.mock('../../../api/models/Credentials');
jest.mock('../../../api/models/InventorySources');
jest.mock('../../../api/models/Projects');

describe('<InventorySourceForm />', () => {
  let wrapper;
  CredentialsAPI.read.mockResolvedValue({
    data: { count: 0, results: [] },
  });
  ProjectsAPI.readInventories.mockResolvedValue({
    data: ['foo', 'bar'],
  });
  InventorySourcesAPI.readOptions.mockResolvedValue({
    data: {
      actions: {
        GET: {
          source: {
            choices: [
              ['file', 'File, Directory or Script'],
              ['scm', 'Sourced from a Project'],
              ['ec2', 'Amazon EC2'],
              ['gce', 'Google Compute Engine'],
              ['azure_rm', 'Microsoft Azure Resource Manager'],
              ['vmware', 'VMware vCenter'],
              ['satellite6', 'Red Hat Satellite 6'],
              ['openstack', 'OpenStack'],
              ['rhv', 'Red Hat Virtualization'],
              ['tower', 'Ansible Tower'],
            ],
          },
        },
      },
    },
  });

  describe('Successful form submission', () => {
    const onSubmit = jest.fn();

    beforeAll(async () => {
      const config = {
        custom_virtualenvs: ['venv/foo', 'venv/bar'],
      };
      await act(async () => {
        wrapper = mountWithContexts(
          <InventorySourceForm onCancel={() => {}} onSubmit={onSubmit} />,
          {
            context: { config },
          }
        );
      });
      await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    });

    afterAll(() => {
      jest.clearAllMocks();
      wrapper.unmount();
    });

    test('should initially display primary form fields', () => {
      expect(wrapper.find('FormGroup[label="Name"]')).toHaveLength(1);
      expect(wrapper.find('FormGroup[label="Description"]')).toHaveLength(1);
      expect(wrapper.find('FormGroup[label="Source"]')).toHaveLength(1);
      expect(
        wrapper.find('FormGroup[label="Ansible Environment"]')
      ).toHaveLength(1);
    });

    test('should display subform when source dropdown has a value', async () => {
      await act(async () => {
        wrapper.find('AnsibleSelect#source').prop('onChange')(null, 'scm');
      });
      wrapper.update();
      expect(wrapper.find('Title').text()).toBe('Source details');
    });

    test('should show field error when form is invalid', async () => {
      expect(onSubmit).not.toHaveBeenCalled();
      await act(async () => {
        wrapper.find('CredentialLookup').invoke('onChange')({
          id: 1,
          name: 'mock cred',
        });
        wrapper.find('ProjectLookup').invoke('onChange')({
          id: 2,
          name: 'mock proj',
        });
        wrapper.find('AnsibleSelect#source_path').prop('onChange')(null, 'foo');
        wrapper.find('AnsibleSelect#verbosity').prop('onChange')(null, '2');
        wrapper.find('button[aria-label="Save"]').simulate('click');
      });
      wrapper.update();
      expect(wrapper.find('FormGroup[label="Name"] .pf-m-error')).toHaveLength(
        1
      );
      expect(onSubmit).not.toHaveBeenCalled();
    });

    test('should call onSubmit when Save button is clicked', async () => {
      expect(onSubmit).not.toHaveBeenCalled();
      wrapper.find('input#name').simulate('change', {
        target: { value: 'new foo', name: 'name' },
      });
      await act(async () => {
        wrapper.find('button[aria-label="Save"]').simulate('click');
      });
      wrapper.update();
      expect(onSubmit).toHaveBeenCalled();
    });
  });

  test('should display ContentError on throw', async () => {
    InventorySourcesAPI.readOptions.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    await act(async () => {
      wrapper = mountWithContexts(
        <InventorySourceForm onCancel={() => {}} onSubmit={() => {}} />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });

  test('calls "onCancel" when Cancel button is clicked', async () => {
    const onCancel = jest.fn();
    await act(async () => {
      wrapper = mountWithContexts(
        <InventorySourceForm onCancel={onCancel} onSubmit={() => {}} />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(onCancel).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Cancel"]').prop('onClick')();
    expect(onCancel).toBeCalled();
  });
});
