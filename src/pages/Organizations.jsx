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

class Organizations extends Component {
  constructor (props) {
    super(props);

    this.state = { organizations: [] };
  }

  componentDidMount () {
    api.getOrganizations()
      .then(({ data }) => this.setState({ organizations: data.results }));
  }

  render () {
    const { light, medium } = PageSectionVariants;
    const { organizations } = this.state;

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
          </Gallery>
        </PageSection>
      </Fragment>
    );
  }
}

export default Organizations;
