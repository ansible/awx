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
        <b>{job.name}</b>
        {/*Heading and Job Stats */}
        {/*Host Status Bar */}
        <OutputToolbar>
          {/* Filter and Pagination */}
          <b>Filter placeholder</b>
          <MenuControls />
        </OutputToolbar>
        <ul>
          <li>
          </li>
        </ul>
      </CardBody>
    );
  }
}

export default JobOutput;
