import React, { Component } from 'react';
import { CardBody } from '@patternfly/react-core';
import MenuControls from './shared/MenuControls';
import styled from 'styled-components';

const OutputToolbar = styled.div`
  display: flex;
  justify-content: space-between;
`;

class JobOutput extends Component {
  render() {
    const { job } = this.props;

    return (
      <CardBody>
        <b>{job.name} - Heading and Job Stats placeholder</b> <br /> {/*Heading and Job Stats */}
        <b>Host Status Bar placeholder</b> <br /> {/*Host Status Bar */}
        <OutputToolbar> {/* Filter and Pagination */}
          <b>Filter placeholder</b>
          <MenuControls />
        </OutputToolbar>
      </CardBody>
    );
  }
}

export default JobOutput;
