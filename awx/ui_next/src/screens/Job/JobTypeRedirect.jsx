import React, { Component } from 'react';
import { Redirect } from 'react-router-dom';
import { UnifiedJobsAPI } from '@api';
import { JOB_TYPE_URL_SEGMENTS } from '../../constants';

class JobTypeRedirect extends Component {
  static defaultProps = {
    view: 'details',
  };

  constructor(props) {
    super(props);

    this.state = {
      hasError: false,
      job: null,
    };
    this.loadJob = this.loadJob.bind(this);
  }

  componentDidMount() {
    this.loadJob();
  }

  async loadJob() {
    const { id } = this.props;
    try {
      const { data } = await UnifiedJobsAPI.read({ id });
      this.setState({
        job: data.results[0],
      });
    } catch (err) {
      this.setState({ hasError: true });
    }
  }

  render() {
    const { path, view } = this.props;
    const { hasError, job } = this.state;

    if (hasError) {
      return <div>Error</div>;
    }
    if (!job) {
      return <div>Loading...</div>;
    }
    const type = JOB_TYPE_URL_SEGMENTS[job.type];
    return <Redirect from={path} to={`/jobs/${type}/${job.id}/${view}`} />;
  }
}

export default JobTypeRedirect;
