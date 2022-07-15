import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { CredentialsAPI } from 'api';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import EC2SubForm from './EC2SubForm';

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

const mockSourceOptions = {
  actions: {
    POST: {},
  },
};

describe('<EC2SubForm />', () => {
  let wrapper;

  beforeEach(async () => {
    CredentialsAPI.read.mockResolvedValue({
      data: { count: 0, results: [] },
    });

    await act(async () => {
      wrapper = mountWithContexts(
        <Formik initialValues={initialValues}>
          <EC2SubForm sourceOptions={mockSourceOptions} />
        </Formik>
      );
    });
  });

  afterAll(() => {
    jest.clearAllMocks();
  });

  test('should render subform fields', () => {
    expect(wrapper.find('FormGroup[label="Credential"]')).toHaveLength(1);
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
      credential_type__namespace: 'aws',
      order_by: 'name',
      page: 1,
      page_size: 5,
    });
  });
});
