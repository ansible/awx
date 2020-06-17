import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import CustomScriptSubForm from './CustomScriptSubForm';
import {
  CredentialsAPI,
  InventoriesAPI,
  InventoryScriptsAPI,
} from '../../../../api';

jest.mock('../../../../api/models/Credentials');
jest.mock('../../../../api/models/Inventories');
jest.mock('../../../../api/models/InventoryScripts');

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({
    id: 789,
  }),
}));

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

describe('<CustomScriptSubForm />', () => {
  let wrapper;
  CredentialsAPI.read.mockResolvedValue({
    data: { count: 0, results: [] },
  });
  InventoriesAPI.readDetail.mockResolvedValue({
    data: { organization: 123 },
  });
  InventoryScriptsAPI.read.mockResolvedValue({
    data: { count: 0, results: [] },
  });

  beforeAll(async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik initialValues={initialValues}>
          <CustomScriptSubForm />
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
    expect(wrapper.find('FormGroup[label="Inventory script"]')).toHaveLength(1);
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
      credential_type__namespace: 'cloud',
      order_by: 'name',
      page: 1,
      page_size: 5,
    });
    expect(InventoriesAPI.readDetail).toHaveBeenCalledTimes(1);
    expect(InventoriesAPI.readDetail).toHaveBeenCalledWith(789);
    expect(InventoryScriptsAPI.read).toHaveBeenCalledTimes(1);
    expect(InventoryScriptsAPI.read).toHaveBeenCalledWith({
      organization: 123,
      role_level: 'admin_role',
      order_by: 'name',
      page: 1,
      page_size: 5,
    });
  });
});
