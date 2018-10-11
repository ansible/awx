import React, { Component } from 'react';
import {
  Card,
  CardHeader,
  CardBody,
} from '@patternfly/react-core';

class OrganizationCard extends Component {
  static title = 'Organization Card';

  constructor (props) {
    super(props);

    const { name } = props.organization;

    this.state = { name };
  }

  render () {
    const { name } = this.state;

    return (
      <Card>
        <CardHeader>{name}</CardHeader>
        <CardBody>Card Body</CardBody>
      </Card>
    );
  }
}

export default OrganizationCard;
