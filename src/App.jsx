import React from 'react';
import { render } from 'react-dom';
import {
  HashRouter as Router,
  Route,
  Link,
  Redirect,
  Switch,
} from 'react-router-dom';
import {
  Brand,
  Nav,
  NavList,
  NavGroup,
  NavItem,
  Page,
  PageHeader,
  PageSidebar,
  Title,
  Toolbar,
  ToolbarGroup,
  ToolbarItem,
} from '@patternfly/react-core';

import api from './api';

import About from './components/About';
import TowerLogo from './components/TowerLogo';

import Applications from './pages/Applications';
import Credentials from './pages/Credentials';
import CredentialTypes from './pages/CredentialTypes';
import Dashboard from './pages/Dashboard';
import InstanceGroups from './pages/InstanceGroups';
import Inventories from './pages/Inventories';
import InventoryScripts from './pages/InventoryScripts';
import Jobs from './pages/Jobs';
import Login from './pages/Login';
import ManagementJobs from './pages/ManagementJobs';
import NotificationTemplates from './pages/NotificationTemplates';
import Organizations from './pages/Organizations';
import Portal from './pages/Portal';
import Projects from './pages/Projects';
import Schedules from './pages/Schedules';
import Settings from './pages/Settings';
import Teams from './pages/Teams';
import Templates from './pages/Templates';
import Users from './pages/Users';


const AuthenticatedRoute = ({ component: Component, ...rest }) => (
  <Route {...rest} render={props => (
    api.isAuthenticated() ? (
      <Component {...props}/>
    ) : (
      <Redirect to={{
        pathname: '/login',
        state: { from: props.location }
      }}/>
    )
  )}/>
);

class App extends React.Component {
  constructor(props) {
    super(props);

    this.state = { activeItem: 'dashboard', isNavOpen: true };
  }

  onNavToggle = () => {
    const { isNavOpen } = this.state;

    this.setState({ isNavOpen: !isNavOpen });
  };

  onNavSelect = ({ itemId }) => {
    this.setState({ activeItem: itemId });
  };

  render() {
    const { activeItem, isNavOpen } = this.state;

    return (
      <Router>
        <Switch>
          <Route path="/login" component={Login} />
          <AuthenticatedRoute component={() => (
            <Page
              header={(
                <PageHeader
                  logo={<TowerLogo />}
                  toolbar={(
                    <Toolbar>
                      <ToolbarGroup>
                        <ToolbarItem>Item 1</ToolbarItem>
                      </ToolbarGroup>
                      <ToolbarGroup>
                        <ToolbarItem>Item 2</ToolbarItem>
                        <ToolbarItem>Item 3</ToolbarItem>
                      </ToolbarGroup>
                    </Toolbar>
                  )}
                  avatar="| avatar"
                  showNavToggle
                  onNavToggle={this.onNavToggle}
                />
              )}
              sidebar={(
                <PageSidebar
                  isNavOpen={isNavOpen}
                  nav={(
                    <Nav onSelect={this.onNavSelect} aria-label="Primary Navigation">
                      <NavGroup title="Views">
                        <NavItem to="#/home" itemId="dashboard" isActive={activeItem === 'dashboard'}>Dashboard</NavItem>
                        <NavItem to="#/jobs" itemId="jobs" isActive={activeItem === 'jobs'}>Jobs</NavItem>
                        <NavItem to="#/schedules" itemId="schedules" isActive={activeItem === 'schedules'}>Schedules</NavItem>
                        <NavItem to="#/portal" itemId="portal" isActive={activeItem === 'portal'}>My View</NavItem>
                      </NavGroup>
                      <NavGroup title="Resources">
                        <NavItem to="#/templates" itemId="templates" isActive={activeItem === 'templates'}>Templates</NavItem>
                        <NavItem to="#/credentials" itemId="credentials" isActive={activeItem === 'credentials'}>Credentials</NavItem>
                        <NavItem to="#/projects" itemId="projects" isActive={activeItem === 'projects'}>Projects</NavItem>
                        <NavItem to="#/inventories" itemId="inventories" isActive={activeItem === 'inventories'}>Inventories</NavItem>
                        <NavItem to="#/inventory_scripts" itemId="inventory_scripts" isActive={activeItem === 'inventory_scripts'}>Inventory Scripts</NavItem>
                      </NavGroup>
                      <NavGroup title="Access">
                        <NavItem to="#/organizations" itemId="organizations" isActive={activeItem === 'organizations'}>Organizations</NavItem>
                        <NavItem to="#/users" itemId="users" isActive={activeItem === 'users'}>Users</NavItem>
                        <NavItem to="#/teams" itemId="teams" isActive={activeItem === 'teams'}>Teams</NavItem>
                      </NavGroup>
                      <NavGroup title="Administration">
                        <NavItem to="#/credential_types" itemId="credential_types" isActive={activeItem === 'credential_types'}>Credential Types</NavItem>
                        <NavItem to="#/notification_templates" itemId="notification_templates" isActive={activeItem === 'notification_templates'}>Notifications</NavItem>
                        <NavItem to="#/management_jobs" itemId="management_jobs" isActive={activeItem === 'management_jobs'}>Management Jobs</NavItem>
                        <NavItem to="#/instance_groups" itemId="instance_groups" isActive={activeItem === 'instance_groups'}>Instance Groups</NavItem>
                        <NavItem to="#/applications" itemId="applications" isActive={activeItem === 'applications'}>Applications</NavItem>
                        <NavItem to="#/settings" itemId="settings" isActive={activeItem === 'settings'}>Settings</NavItem>
                      </NavGroup>
                    </Nav>
                  )}
                />
              )}>
              <Switch>
                <Route exact path="/" component={() => (<Redirect to="/home" />)} />
                <Route path="/home" component={Dashboard} />
                <Route path="/jobs" component={Jobs} />
                <Route path="/schedules" component={Schedules} />
                <Route path="/portal" component={Portal} />
                <Route path="/templates" component={Templates} />
                <Route path="/credentials" component={Credentials} />
                <Route path="/projects" component={Projects} />
                <Route path="/inventories" component={Inventories} />
                <Route path="/inventory_scripts" component={InventoryScripts} />
                <Route path="/organizations" component={Organizations} />
                <Route path="/users" component={Users} />
                <Route path="/teams" component={Teams} />
                <Route path="/credential_types" component={CredentialTypes} />
                <Route path="/notification_templates" component={NotificationTemplates} />
                <Route path="/management_jobs" component={ManagementJobs} />
                <Route path="/instance_groups" component={InstanceGroups} />
                <Route path="/applications" component={Applications} />
                <Route path="/settings" component={Settings} />
              </Switch>
            </Page>
          )} />
        </Switch>
      </Router>
    );
  }
}

const el = document.getElementById('app');

render(<App />, el);
