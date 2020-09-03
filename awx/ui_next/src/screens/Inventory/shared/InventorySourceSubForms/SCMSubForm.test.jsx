import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import SCMSubForm from './SCMSubForm';
import { ProjectsAPI, CredentialsAPI } from '../../../../api';

jest.mock('../../../../api/models/Projects');
jest.mock('../../../../api/models/Credentials');

const initialValues = {
  credential: null,
  custom_virtualenv: '',
  overwrite: false,
  overwrite_vars: false,
  source_path: '',
  source_project: null,
  source_script: null,
  source_vars: '---\n',
  update_cache_timeout: 0,
  update_on_launch: true,
  update_on_project_update: false,
  verbosity: 1,
};

describe('<SCMSubForm />', () => {
  let wrapper;
  CredentialsAPI.read.mockResolvedValue({
    data: { count: 0, results: [] },
  });
  ProjectsAPI.readInventories.mockResolvedValue({
    data: ['foo', 'bar'],
  });
  ProjectsAPI.read.mockResolvedValue({
    data: {
      count: 2,
      results: [
        {
          id: 1,
          name: 'mock proj one',
        },
        {
          id: 2,
          name: 'mock proj two',
        },
      ],
    },
  });

  beforeAll(async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik initialValues={initialValues}>
          <SCMSubForm />
        </Formik>
      );
    });
  });

  afterAll(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('should render subform fields', () => {
    expect(wrapper.find('FormGroup[label="Credential"]')).toHaveLength(1);
    expect(wrapper.find('FormGroup[label="Project"]')).toHaveLength(1);
    expect(wrapper.find('FormGroup[label="Inventory file"]')).toHaveLength(1);
    expect(wrapper.find('FormGroup[label="Verbosity"]')).toHaveLength(1);
    expect(wrapper.find('FormGroup[label="Update options"]')).toHaveLength(1);
    expect(
      wrapper.find('FormGroup[label="Cache timeout (seconds)"]')
    ).toHaveLength(1);
    expect(
      wrapper.find('VariablesField[label="Source variables"]')
    ).toHaveLength(1);
  });

  test('project lookup should fetch project source path list', async () => {
    expect(ProjectsAPI.readInventories).not.toHaveBeenCalled();
    await act(async () => {
      wrapper.find('ProjectLookup').invoke('onChange')({
        id: 2,
        name: 'mock proj two',
      });
      wrapper.find('ProjectLookup').invoke('onBlur')();
    });
    expect(ProjectsAPI.readInventories).toHaveBeenCalledWith(2);
  });

  test('changing source project should reset source path dropdown', async () => {
    expect(wrapper.find('AnsibleSelect#source_path').prop('value')).toEqual('');

    await act(async () => {
      await wrapper.find('AnsibleSelect#source_path').prop('onChange')(
        null,
        'bar'
      );
    });
    wrapper.update();
    expect(wrapper.find('AnsibleSelect#source_path').prop('value')).toEqual(
      'bar'
    );

    await act(async () => {
      wrapper.find('ProjectLookup').invoke('onChange')({
        id: 1,
        name: 'mock proj one',
      });
    });
    wrapper.update();
    expect(wrapper.find('AnsibleSelect#source_path').prop('value')).toEqual('');
  });
});
