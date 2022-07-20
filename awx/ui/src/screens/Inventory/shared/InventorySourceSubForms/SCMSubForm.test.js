import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { ProjectsAPI, CredentialsAPI } from 'api';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import SCMSubForm from './SCMSubForm';

jest.mock('../../../../api');

const initialValues = {
  credential: null,
  overwrite: false,
  overwrite_vars: false,
  source_path: '',
  source_project: null,
  source_script: null,
  source_vars: '---\n',
  update_cache_timeout: 0,
  update_on_launch: true,
  verbosity: 1,
};

describe('<SCMSubForm />', () => {
  let wrapper;

  beforeEach(async () => {
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
    expect(wrapper.find('Select#source_path').prop('selections')).toEqual('');
    await act(async () => {
      await wrapper.find('Select#source_path').prop('onToggle')();
    });
    wrapper.update();
    await act(async () => {
      await wrapper.find('Select#source_path').prop('onSelect')(null, 'bar');
    });
    wrapper.update();
    expect(wrapper.find('Select#source_path').prop('selections')).toEqual(
      'bar'
    );

    await act(async () => {
      wrapper.find('ProjectLookup').invoke('onChange')({
        id: 1,
        name: 'mock proj one',
      });
    });
    wrapper.update();
    expect(wrapper.find('Select#source_path').prop('selections')).toEqual('');
  });

  test('should be able to create custom source path', async () => {
    const customInitialValues = {
      credential: { id: 1, name: 'Credential' },
      overwrite: false,
      overwrite_vars: false,
      source_path: '/path',
      source_project: { id: 1, name: 'Source project' },
      source_script: null,
      source_vars: '---\n',
      update_cache_timeout: 0,
      update_on_launch: true,
      verbosity: 1,
    };
    let customWrapper;
    await act(async () => {
      customWrapper = mountWithContexts(
        <Formik initialValues={customInitialValues}>
          <SCMSubForm />
        </Formik>
      );
    });

    await act(async () => {
      customWrapper.find('Select').invoke('onSelect')({}, 'newPath');
    });
    customWrapper.update();
    expect(customWrapper.find('Select').prop('selections')).toBe('newPath');
  });
});
