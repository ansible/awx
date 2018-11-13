import React, { Fragment } from 'react';
import {
  HashRouter as Router,
  Redirect,
  Switch,
} from 'react-router-dom';

import {
  BackgroundImage,
  BackgroundImageSrc,
  Nav,
  NavExpandable,
  NavList,
  NavItem,
  Page,
  PageHeader,
  PageSidebar,
  Toolbar,
  ToolbarGroup,
  ToolbarItem
} from '@patternfly/react-core';
import { global_breakpoint_md as breakpointMd } from '@patternfly/react-tokens';

import api from './api';
import { API_LOGOUT } from './endpoints';

// import About from './components/About';
import LogoutButton from './components/LogoutButton';
import TowerLogo from './components/TowerLogo';
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
import AuthSettings from './pages/AuthSettings';
import JobsSettings from './pages/JobsSettings';
import SystemSettings from './pages/SystemSettings';
import UISettings from './pages/UISettings';
import License from './pages/License';
import Teams from './pages/Teams';
import Templates from './pages/Templates';
import Users from './pages/Users';

class App extends React.Component {
  constructor (props) {
    super(props);

    const isNavOpen = typeof window !== 'undefined' && window.innerWidth >= parseInt(breakpointMd.value, 10);
    this.state = {
      isNavOpen,
      activeGroup: 'views_group',
      activeItem: 'views_group_dashboard'
    };
  }

  onNavSelect = result => {
    this.setState({
      activeItem: result.itemId,
      activeGroup: result.groupId
    });
  };

  onNavToggle = () => {
    this.setState(({ isNavOpen }) => ({ isNavOpen: !isNavOpen }));
  };

  onLogoClick = () => {
    this.setState({ activeGroup: 'views_group', activeItem: 'views_group_dashboard' });
  }

  onDevLogout = async () => {
    await api.get(API_LOGOUT);
    this.setState({ activeGroup: 'views_group', activeItem: 'views_group_dashboard' });
  }

  render () {
    const { activeItem, activeGroup, isNavOpen } = this.state;
    const { logo, loginInfo } = this.props;

    const PageToolbar = (
      <Toolbar>
        <ToolbarGroup>
          <ToolbarItem>
            <LogoutButton onDevLogout={() => this.onDevLogout()} />
          </ToolbarItem>
        </ToolbarGroup>
      </Toolbar>
    );

    return (
      <Router>
        <Fragment>
          <BackgroundImage
            src={{
              [BackgroundImageSrc.lg]: '/assets/images/pfbg_1200.jpg',
              [BackgroundImageSrc.md]: '/assets/images/pfbg_992.jpg',
              [BackgroundImageSrc.md2x]: '/assets/images/pfbg_992@2x.jpg',
              [BackgroundImageSrc.sm]: '/assets/images/pfbg_768.jpg',
              [BackgroundImageSrc.sm2x]: '/assets/images/pfbg_768@2x.jpg',
              [BackgroundImageSrc.xl]: '/assets/images/pfbg_2000.jpg',
              [BackgroundImageSrc.xs]: '/assets/images/pfbg_576.jpg',
              [BackgroundImageSrc.xs2x]: '/assets/images/pfbg_576@2x.jpg',
              [BackgroundImageSrc.filter]: '/assets/images/background-filter.svg'
            }}
          />
          <Switch>
            <ConditionalRedirect shouldRedirect={() => api.isAuthenticated()} redirectPath="/" path="/login" component={() => <Login logo={logo} loginInfo={loginInfo} />} />
            <Fragment>
              <Page
                header={(
                  <PageHeader
                    logo={<TowerLogo onClick={this.onLogoClick} />}
                    toolbar={PageToolbar}
                    showNavToggle
                    onNavToggle={this.onNavToggle}
                  />
                )}
                sidebar={(
                  <PageSidebar
                    isNavOpen={isNavOpen}
                    nav={(
                      <Nav onSelect={this.onNavSelect} aria-label="Primary Navigation">
                        <NavList>
                          <NavExpandable
                            title="Views"
                            groupId="views_group"
                            isActive={activeGroup === 'views_group'}
                            isExpanded={activeGroup === 'views_group'}
                          >
                            <NavItem
                              to="#/home"
                              groupId="views_group"
                              itemId="views_group_dashboard"
                              isActive={activeItem === 'views_group_dashboard'}
                            >
                              Dashboard
                            </NavItem>
                            <NavItem
                              to="#/jobs"
                              groupId="views_group"
                              itemId="views_group_jobs"
                              isActive={activeItem === 'views_group_jobs'}
                            >
                              Jobs
                            </NavItem>
                            <NavItem
                              to="#/schedules"
                              groupId="views_group"
                              itemId="views_group_schedules"
                              isActive={activeItem === 'views_group_schedules'}
                            >
                              Schedules
                            </NavItem>
                            <NavItem
                              to="#/portal"
                              groupId="views_group"
                              itemId="views_group_portal"
                              isActive={activeItem === 'views_group_portal'}
                            >
                              My View
                            </NavItem>
                          </NavExpandable>
                          <NavExpandable
                            title="Resources"
                            groupId="resources_group"
                            isActive={activeGroup === 'resources_group'}
                            isExpanded={activeGroup === 'resources_group'}
                          >
                            <NavItem
                              to="#/templates"
                              groupId="resources_group"
                              itemId="resources_group_templates"
                              isActive={activeItem === 'resources_group_templates'}
                            >
                              Templates
                            </NavItem>
                            <NavItem
                              to="#/credentials"
                              groupId="resources_group"
                              itemId="resources_group_credentials"
                              isActive={activeItem === 'resources_group_credentials'}
                            >
                              Credentials
                            </NavItem>
                            <NavItem
                              to="#/projects"
                              groupId="resources_group"
                              itemId="resources_group_projects"
                              isActive={activeItem === 'resources_group_projects'}
                            >
                              Projects
                            </NavItem>
                            <NavItem
                              to="#/inventories"
                              groupId="resources_group"
                              itemId="resources_group_inventories"
                              isActive={activeItem === 'resources_group_inventories'}
                            >
                              Inventories
                            </NavItem>
                            <NavItem
                              to="#/inventory_scripts"
                              groupId="resources_group"
                              itemId="resources_group_inventory_scripts"
                              isActive={activeItem === 'resources_group_inventory_scripts'}
                            >
                              Inventory Scripts
                            </NavItem>
                          </NavExpandable>
                          <NavExpandable
                            title="Access"
                            groupId="access_group"
                            isActive={activeGroup === 'access_group'}
                            isExpanded={activeGroup === 'access_group'}
                          >
                            <NavItem
                              to="#/organizations"
                              groupId="access_group"
                              itemId="access_group_organizations"
                              isActive={activeItem === 'access_group_organizations'}
                            >
                              Organizations
                            </NavItem>
                            <NavItem
                              to="#/users"
                              groupId="access_group"
                              itemId="access_group_users"
                              isActive={activeItem === 'access_group_users'}
                            >
                              Users
                            </NavItem>
                            <NavItem
                              to="#/teams"
                              groupId="access_group"
                              itemId="access_group_teams"
                              isActive={activeItem === 'access_group_teams'}
                            >
                              Teams
                            </NavItem>
                          </NavExpandable>
                          <NavExpandable
                            title="Administration"
                            groupId="administration_group"
                            isActive={activeGroup === 'administration_group'}
                            isExpanded={activeGroup === 'administration_group'}
                          >
                            <NavItem
                              to="#/credential_types"
                              groupId="administration_group"
                              itemId="administration_group_credential_types"
                              isActive={activeItem === 'administration_group_credential_types'}
                            >
                              Credential Types
                            </NavItem>
                            <NavItem
                              to="#/notification_templates"
                              groupId="administration_group"
                              itemId="administration_group_notification_templates"
                              isActive={activeItem === 'administration_group_notification_templates'}
                            >
                              Notification Templates
                            </NavItem>
                            <NavItem
                              to="#/management_jobs"
                              groupId="administration_group"
                              itemId="administration_group_management_jobs"
                              isActive={activeItem === 'administration_group_management_jobs'}
                            >
                              Management Jobs
                            </NavItem>
                            <NavItem
                              to="#/instance_groups"
                              groupId="administration_group"
                              itemId="administration_group_instance_groups"
                              isActive={activeItem === 'administration_group_instance_groups'}
                            >
                              Instance Groups
                            </NavItem>
                            <NavItem
                              to="#/applications"
                              groupId="administration_group"
                              itemId="administration_group_applications"
                              isActive={activeItem === 'administration_group_applications'}
                            >
                              Applications
                            </NavItem>
                          </NavExpandable>
                          <NavExpandable
                            title="Settings"
                            groupId="settings_group"
                            isActive={activeGroup === 'settings_group'}
                            isExpanded={activeGroup === 'settings_group'}
                          >
                            <NavItem
                              to="#/auth_settings"
                              groupId="settings_group"
                              itemId="settings_group_auth"
                              isActive={activeItem === 'settings_group_auth'}
                            >
                              Authentication
                            </NavItem>
                            <NavItem
                              to="#/jobs_settings"
                              groupId="settings_group"
                              itemId="settings_group_jobs"
                              isActive={activeItem === 'settings_group_jobs'}
                            >
                              Jobs
                            </NavItem>
                            <NavItem
                              to="#/system_settings"
                              groupId="settings_group"
                              itemId="settings_group_system"
                              isActive={activeItem === 'settings_group_system'}
                            >
                              System
                            </NavItem>
                            <NavItem
                              to="#/ui_settings"
                              groupId="settings_group"
                              itemId="settings_group_ui"
                              isActive={activeItem === 'settings_group_ui'}
                            >
                              User Interface
                            </NavItem>
                          </NavExpandable>
                        </NavList>
                      </Nav>
                    )}
                  />
                )}
                useCondensed
              >
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
                <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/auth_settings" component={AuthSettings} />
                <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/jobs_settings" component={JobsSettings} />
                <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/system_settings" component={SystemSettings} />
                <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/ui_settings" component={UISettings} />
                <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/license" component={License} />
              </Page>
            </Fragment>
          </Switch>
        </Fragment>
      </Router>
    );
  }
}

export default App;
