import React, { Component, Fragment } from 'react';
import {
  Gallery,
  GalleryItem,
  PageSection,
  PageSectionVariants,
  Title,
} from '@patternfly/react-core';

import OrganizationCard from '../components/OrganizationCard';
import api from '../api';
import { API_ORGANIZATIONS } from '../endpoints';

class Organizations extends Component {
  constructor (props) {
    super(props);

    this.state = {
      organizations: [],
      error: false,
    };
  }

  async componentDidMount () {
    try {
      const { data } = await api.get(API_ORGANIZATIONS);
      this.setState({ organizations: data.results });
    } catch (err) {
      this.setState({ error: err });
    }
  }

  render () {
    const { light, medium } = PageSectionVariants;
    const { organizations, error } = this.state;

    return (
      <Fragment>
        <PageSection variant={light} className="pf-m-condensed">
          <Title size="2xl">Organizations</Title>
        </PageSection>
        <PageSection variant={medium}>
          <Gallery gutter="md">
            {organizations.map(o => (
              <GalleryItem key={o.id}>
                <OrganizationCard key={o.id} organization={o} />
              </GalleryItem>
            ))}
            { error ? <div>error</div> : '' }
          </Gallery>
        </PageSection>
      </Fragment>
    );
  }
}

export default Organizations;
