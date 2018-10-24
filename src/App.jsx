import React, { Fragment } from 'react';
import {
  HashRouter as Router,
  Route,
  Link,
  Redirect,
  Switch,
} from 'react-router-dom';

import {
  BackgroundImage,
  BackgroundImageSrc,
  Brand,
  Button,
  ButtonVariant,
  Nav,
  NavExpandable,
  NavGroup,
  NavItem,
  Page,
  PageHeader,
  PageSection,
  PageSectionVariants,
  PageSidebar,
  TextContent,
  Text,
  Toolbar,
  ToolbarGroup,
  ToolbarItem
} from '@patternfly/react-core';
import { global_breakpoint_md as breakpointMd } from '@patternfly/react-tokens';
import { css } from '@patternfly/react-styles';

import api from './api';

import About from './components/About';
import TowerLogo from './components/TowerLogo';
// import AuthenticatedRoute from './components/AuthenticatedRoute';
// import UnauthenticatedRoute from './components/UnauthenticatedRoute';
import ConditionalRedirect from './components/ConditionalRedirect';

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

class App extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      activeItem: window.location.hash.split("#/").pop().split("/").shift(),
      isNavOpen: (typeof window !== 'undefined' &&
        window.innerWidth >= parseInt(breakpointMd.value, 10)),
    };

    this.state.activeGroup = this.state.activeItem.startsWith("settings_group_") ? "settings": "";
  }

  onNavToggle = () => {
    const { isNavOpen } = this.state;

    this.setState({ isNavOpen: !isNavOpen });
  }

  onNavSelect = ({ groupId, itemId }) => {
    this.setState({ activeGroup: groupId || "", activeItem: itemId });
  };

  onLogoClick = () => {
    this.setState({ activeItem: "dashboard" });
  }

  onDevLogout = () => {
    api.logout()
      .then(() => {
        this.setState({ activeItem: "dashboard" });
      })
  }

  render() {
    const { activeItem, activeGroup, isNavOpen } = this.state;
    const { logo, loginInfo } = this.props;

    return (
      <Router>
        <Fragment>
          <BackgroundImage src={{
            [BackgroundImageSrc.lg]: '/assets/images/pfbg_1200.jpg',
            [BackgroundImageSrc.md]: '/assets/images/pfbg_992.jpg',
            [BackgroundImageSrc.md2x]: '/assets/images/pfbg_992@2x.jpg',
            [BackgroundImageSrc.sm]: '/assets/images/pfbg_768.jpg',
            [BackgroundImageSrc.sm2x]: '/assets/images/pfbg_768@2x.jpg',
            [BackgroundImageSrc.xl]: '/assets/images/pfbg_2000.jpg',
            [BackgroundImageSrc.xs]: '/assets/images/pfbg_576.jpg',
            [BackgroundImageSrc.xs2x]: '/assets/images/pfbg_576@2x.jpg',
            [BackgroundImageSrc.filter]: '/assets/images/background-filter.svg'
          }} />
          <Switch>
            <ConditionalRedirect shouldRedirect={() => api.isAuthenticated()} redirectPath="/" path="/login" component={() => <Login logo={logo} loginInfo={loginInfo} />} />
            <Fragment>
              <Page
                header={(
                  <PageHeader
                    logo={<TowerLogo onClick={this.onLogoClick} />}
                    avatar={<i className="fas fa-user" onClick={this.onDevLogout}></i>}
                    showNavToggle
                    onNavToggle={this.onNavToggle}
                  />
                )}
                sidebar={(
                  <PageSidebar
                    isNavOpen={isNavOpen}
                    nav={(
                      <Nav aria-label="Primary Navigation">
                        <NavGroup title="Views">
                          <NavItem to="#/home" itemId="dashboard" isActive={activeItem ==='home'}>Dashboard</NavItem>
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
                          <NavExpandable title="Settings" groupId="settings_group" isActive={activeGroup === 'settings_group'}>
                            <NavItem to="#/settings/auth" groupId="settings_group" itemId="settings_group_auth" isActive={activeItem === 'settings_group_auth'}>
                              Authentication
                            </NavItem>
                            <NavItem to="#/settings/jobs" groupId="settings_group" itemId="settings_group_jobs" isActive={activeItem === 'settings_group_jobs'}>
                              Jobs
                            </NavItem>
                            <NavItem to="#/settings/system" groupId="settings_group" itemId="settings_group_system" isActive={activeItem === 'settings_group_system'}>
                              System
                            </NavItem>
                            <NavItem to="#/settings/ui" groupId="settings_group" itemId="settings_group_ui" isActive={activeItem === 'settings_group_ui'}>
                              User Interface
                            </NavItem>
                          </NavExpandable>
                        </NavGroup>
                      </Nav>
                    )}
                  />
                )}>
                <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" exact path="/" component={() => (<Redirect to="/home" />)} />
                <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/home" component={Dashboard} />
                <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/jobs" component={Jobs} />
                <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/schedules" component={Schedules} />
                <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/portal" component={Portal} />
                <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/templates" component={Templates} />
                <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/credentials" component={Credentials} />
                <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/projects" component={Projects} />
                <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/inventories" component={Inventories} />
                <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/inventory_scripts" component={InventoryScripts} />
                <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/organizations" component={Organizations} />
                <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/users" component={Users} />
                <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/teams" component={Teams} />
                <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/credential_types" component={CredentialTypes} />
                <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/notification_templates" component={NotificationTemplates} />
                <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/management_jobs" component={ManagementJobs} />
                <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/instance_groups" component={InstanceGroups} />
                <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/applications" component={Applications} />
                <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/settings" component={Settings} />
              </Page>
            </Fragment>
          </Switch>
        </Fragment>
      </Router>
    );
  }
}

export default App;
