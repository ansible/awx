import React, { Component } from 'react';
import { CardBody  } from '@patternfly/react-core';


class JobOutput extends Component {
  constructor (props) {
    super(props);
  }

  render () {
    const {
      job
    } = this.props;

    return (
      <CardBody>
        <b>{job.name}</b>
      </CardBody>
    );
  }
}

export default JobOutput;
