import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import { Formik } from 'formik';
import SCMSubForm from './SCMSubForm';
import { ProjectsAPI } from '@api';

jest.mock('@api/models/Projects');

const initialValues = {
  credential: null,
  custom_virtualenv: '',
  overwrite: false,
  overwrite_vars: false,
  source_path: '',
  source_project: null,
  source_vars: '---\n',
  update_cache_timeout: 0,
  update_on_launch: false,
  update_on_project_update: false,
  verbosity: 1,
};

describe('<SCMSubForm />', () => {
  let wrapper;

  ProjectsAPI.readInventories.mockResolvedValue({
    data: ['foo'],
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
      wrapper.find('VariablesField[label="Environment variables"]')
    ).toHaveLength(1);
  });

  test('project lookup should fetch project source path list', async () => {
    expect(ProjectsAPI.readInventories).not.toHaveBeenCalled();
    await act(async () => {
      wrapper.find('ProjectLookup').invoke('onChange')({
        id: 2,
        name: 'mock proj',
      });
      wrapper.find('ProjectLookup').invoke('onBlur')();
    });
    expect(ProjectsAPI.readInventories).toHaveBeenCalledWith(2);
  });
});
