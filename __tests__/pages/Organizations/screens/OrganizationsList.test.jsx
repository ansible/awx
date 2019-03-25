import React from 'react';
import { mount } from 'enzyme';
import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';
import OrganizationsList from '../../../../src/pages/Organizations/screens/OrganizationsList';

const mockAPIOrgsList = {
  data: {
    results: [{
      name: 'Organization 0',
      id: 1,
      summary_fields: {
        related_field_counts: {
          teams: 3,
          users: 4
        }
      },
    },
    {
      name: 'Organization 1',
      id: 1,
      summary_fields: {
        related_field_counts: {
          teams: 2,
          users: 5
        }
      },
    },
    {
      name: 'Organization 2',
      id: 2,
      summary_fields: {
        related_field_counts: {
          teams: 5,
          users: 6
        }
      },
    }]
  },
  isModalOpen: false,
  warningTitle: 'title',
  warningMsg: 'message'

};

describe('<OrganizationsList />', () => {
  test('initially renders succesfully', () => {
    mount(
      <MemoryRouter initialEntries={['/organizations']} initialIndex={0}>
        <I18nProvider>
          <OrganizationsList
            match={{ path: '/organizations', url: '/organizations' }}
            location={{ search: '', pathname: '/organizations' }}
          />
        </I18nProvider>
      </MemoryRouter>
    );
  });

  test.only('Modal closes when close button is clicked.', async (done) => {
    const handleClearOrgsToDelete = jest.fn();
    const wrapper = mount(
      <MemoryRouter initialEntries={['/organizations']} initialIndex={0}>
        <I18nProvider>
          <OrganizationsList
            match={{ path: '/organizations', url: '/organizations' }}
            location={{ search: '', pathname: '/organizations' }}
            getItems={({ data: { orgsToDelete: [{ name: 'Organization 1', id: 1 }] } })}
            handleClearOrgsToDelete={handleClearOrgsToDelete()}
          />
        </I18nProvider>
      </MemoryRouter>
    );
    wrapper.find({ type: 'checkbox' }).simulate('click');
    wrapper.find('button[aria-label="Delete"]').simulate('click');

    wrapper.find('DataListToolbar').prop('onOpenDeleteModal')();
    expect(wrapper.find('OrganizationsList').state().isModalOpen).toEqual(true);
    setImmediate(() => {
      wrapper.update();
      wrapper.setState({
        selected: mockAPIOrgsList.data.results.map((result) => result.id),
        orgsToDelete: mockAPIOrgsList.data.results.map((result) => result),
        isModalOpen: true,
      });

      wrapper.find('button[aria-label="Close"]').simulate('click');
      expect(handleClearOrgsToDelete).toBeCalled();
      const list = wrapper.find('OrganizationsList');
      expect(list.state().isModalOpen).toBe(false);
      done();
    });
  });

  test.only('Orgs to delete length is 0 when all orgs are selected and Delete button is called.', async (done) => {
    const handleClearOrgsToDelete = jest.fn();
    const handleOrgDelete = jest.fn();
    const fetchOrganizations = jest.fn();
    const wrapper = mount(
      <MemoryRouter initialEntries={['/organizations']} initialIndex={0}>
        <I18nProvider>
          <OrganizationsList
            match={{ path: '/organizations', url: '/organizations' }}
            location={{ search: '', pathname: '/organizations' }}
            getItems={({ data: { orgsToDelete: [{ name: 'Organization 1', id: 1 }] } })}
            handleClearOrgsToDelete={handleClearOrgsToDelete()}
            handleOrgDelete={handleOrgDelete()}
            fetchOrganizations={fetchOrganizations()}

          />
        </I18nProvider>
      </MemoryRouter>
    );
    wrapper.find({ type: 'checkbox' }).simulate('click');
    wrapper.find('button[aria-label="Delete"]').simulate('click');

    wrapper.find('DataListToolbar').prop('onOpenDeleteModal')();
    expect(wrapper.find('OrganizationsList').state().isModalOpen).toEqual(true);
    setImmediate(() => {
      wrapper.update();
      wrapper.setState({
        selected: mockAPIOrgsList.data.results.map((result) => result.id),
        orgsToDelete: mockAPIOrgsList.data.results.map((result) => result),
        isModalOpen: true,
      });
      wrapper.update();

      const list = wrapper.find('OrganizationsList');
      wrapper.find('button[aria-label="confirm-delete"]').simulate('click');
      expect(list.state().orgsToDelete.length).toEqual(list.state().orgsDeleted.length);
      expect(fetchOrganizations).toHaveBeenCalled();
      expect(list.state().results).toHaveLength(0);
      done();
    });
  });
});
