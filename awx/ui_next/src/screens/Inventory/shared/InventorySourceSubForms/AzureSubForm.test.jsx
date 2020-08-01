import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import AzureSubForm from './AzureSubForm';
import { CredentialsAPI } from '../../../../api';

jest.mock('../../../../api/models/Credentials');

const initialValues = {
  credential: null,
  custom_virtualenv: '',
  group_by: '',
  instance_filters: '',
  overwrite: false,
  overwrite_vars: false,
  source_path: '',
  source_project: null,
  source_regions: '',
  source_script: null,
  source_vars: '---\n',
  update_cache_timeout: 0,
  update_on_launch: true,
  update_on_project_update: false,
  verbosity: 1,
};

const mockSourceOptions = {
  actions: {
    POST: {
      source_regions: {
        azure_rm_region_choices: [],
      },
    },
  },
};

describe('<AzureSubForm />', () => {
  let wrapper;
  CredentialsAPI.read.mockResolvedValue({
    data: { count: 0, results: [] },
  });

  beforeAll(async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik initialValues={initialValues}>
          <AzureSubForm sourceOptions={mockSourceOptions} />
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
    expect(wrapper.find('FormGroup[label="Regions"]')).toHaveLength(1);
    expect(wrapper.find('FormGroup[label="Verbosity"]')).toHaveLength(1);
    expect(wrapper.find('FormGroup[label="Update options"]')).toHaveLength(1);
    expect(
      wrapper.find('FormGroup[label="Cache timeout (seconds)"]')
    ).toHaveLength(1);
    expect(
      wrapper.find('VariablesField[label="Source variables"]')
    ).toHaveLength(1);
  });

  test('should make expected api calls', () => {
    expect(CredentialsAPI.read).toHaveBeenCalledTimes(1);
    expect(CredentialsAPI.read).toHaveBeenCalledWith({
      credential_type__namespace: 'azure_rm',
      order_by: 'name',
      page: 1,
      page_size: 5,
    });
  });
});
