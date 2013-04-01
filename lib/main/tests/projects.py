# (c) 2013, AnsibleWorks
#
# This file is part of Ansible Commander
#
# Ansible Commander is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible Commander is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible Commander.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import json

from django.contrib.auth.models import User as DjangoUser
import django.test
from django.test.client import Client
from lib.main.models import *
from lib.main.tests.base import BaseTest

class ProjectsTest(BaseTest):

    # tests for users, projects, and teams

    def collection(self):
        return '/api/v1/projects/'

    def setUp(self):
        super(ProjectsTest, self).setUp()
        self.setup_users()
 
        self.organizations = self.make_organizations(self.super_django_user, 10)
        self.projects      = self.make_projects(self.normal_django_user, 10)

        # add projects to organizations in a more or less arbitrary way
        for project in self.projects[0:2]:
            self.organizations[0].projects.add(project)
        for project in self.projects[3:8]:
            self.organizations[1].projects.add(project)
        for project in self.projects[9:10]: 
            self.organizations[2].projects.add(project)
        self.organizations[0].projects.add(self.projects[-1])
        self.organizations[9].projects.add(self.projects[-2])

        # get the URL for various organization records
        self.a_detail_url  = "%s%s" % (self.collection(), self.organizations[0].pk)
        self.b_detail_url  = "%s%s" % (self.collection(), self.organizations[1].pk)
        self.c_detail_url  = "%s%s" % (self.collection(), self.organizations[2].pk)

        # configuration:
        #   admin_user is an admin and regular user in all organizations
        #   other_user is all organizations
        #   normal_user is a user in organization 0, and an admin of organization 1

        for x in self.organizations:
            # NOTE: superuser does not have to be explicitly added to admin group
            # x.admins.add(self.super_django_user)
            x.users.add(self.super_django_user)
 
        self.organizations[0].users.add(self.normal_django_user)
        self.organizations[1].admins.add(self.normal_django_user)

        self.team1 = Team.objects.create(
            name = 'team1', organization = self.organizations[0]
        )

        self.team2 = Team.objects.create(
            name = 'team2', organization = self.organizations[0]
        )

        # create some teams in the first org
        self.team1.projects.add(self.projects[0])
        self.team2.projects.add(self.projects[1])
        self.team2.projects.add(self.projects[2])
        self.team2.projects.add(self.projects[3])
        self.team2.projects.add(self.projects[4])
        self.team2.projects.add(self.projects[5])
        self.team1.save()
        self.team2.save()
        self.team1.users.add(self.normal_django_user)
        self.team2.users.add(self.other_django_user)

        self.nobody_django_user = User.objects.create(username='nobody')
        self.nobody_django_user.set_password('nobody')
        self.nobody_django_user.save()

    def get_nobody_credentials(self):
        # here is a user without any permissions...
        return ('nobody', 'nobody')

    def test_mainline(self):

        # =====================================================================
        # PROJECTS - LISTING

        # can get projects list
        projects = '/api/v1/projects/'
        # invalid auth
        self.get(projects, expect=401)
        self.get(projects, expect=401, auth=self.get_invalid_credentials())
        # super user
        results = self.get(projects, expect=200, auth=self.get_super_credentials())
        self.assertEquals(results['count'], 10)
        # org admin
        results = self.get(projects, expect=200, auth=self.get_normal_credentials())
        self.assertEquals(results['count'], 6)
        # user on a team
        results = self.get(projects, expect=200, auth=self.get_other_credentials())
        self.assertEquals(results['count'], 5)
        # user not on any teams
        results = self.get(projects, expect=200, auth=self.get_nobody_credentials())
        self.assertEquals(results['count'], 0)       
 
        # =====================================================================
        # PROJECTS - ACCESS
        project = '/api/v1/projects/%s/' % self.projects[3].pk
        self.get(project, expect=200, auth=self.get_super_credentials())
        self.get(project, expect=200, auth=self.get_normal_credentials())
        self.get(project, expect=403, auth=self.get_other_credentials())
        self.get(project, expect=403, auth=self.get_nobody_credentials())

        # can delete projects
        self.delete(project, expect=204, auth=self.get_normal_credentials())
        self.get(project, expect=404, auth=self.get_normal_credentials())

        # can list member organizations for projects
        proj_orgs = '/api/v1/projects/1/organizations/'
        # only usable as superuser
        got = self.get(proj_orgs, expect=403, auth=self.get_normal_credentials())
        got = self.get(proj_orgs, expect=200, auth=self.get_super_credentials())
        self.assertEquals(got['count'], 1)
        self.assertEquals(got['results'][0]['url'], '/api/v1/organizations/1/')
        # you can't add organizations to projects here, verify that this is true (405)
        self.post(proj_orgs, data={}, expect=405, auth=self.get_super_credentials())

        # =====================================================================
        # TEAMS

        all_teams = '/api/v1/teams/'
        team1 = '/api/v1/teams/1/'

        # can list teams
        got = self.get(all_teams, expect=200, auth=self.get_super_credentials())
        self.assertEquals(got['count'], 2)
        # FIXME: for other accounts, also check filtering

        # can get teams
        got = self.get(team1, expect=200, auth=self.get_super_credentials())
        self.assertEquals(got['url'], '/api/v1/teams/1/')
        got = self.get(team1, expect=200, auth=self.get_normal_credentials())
        got = self.get(team1, expect=403, auth=self.get_other_credentials())
        self.team1.users.add(User.objects.get(username='other'))
        self.team1.save()
        got = self.get(team1, expect=200, auth=self.get_other_credentials())
        got = self.get(team1, expect=403, auth=self.get_nobody_credentials())

        new_team  = dict(name='newTeam',  description='blarg', organization=1)        
        new_team2 = dict(name='newTeam2', description='blarg', organization=1)
        new_team3 = dict(name='newTeam3', description='bad wolf', organization=1)

        # can add teams
        posted1 = self.post(all_teams, data=new_team, expect=201, auth=self.get_super_credentials())
        posted2 = self.post(all_teams, data=new_team, expect=400, auth=self.get_super_credentials())
        posted3 = self.post(all_teams, data=new_team2, expect=201, auth=self.get_normal_credentials())
        posted4 = self.post(all_teams, data=new_team2, expect=400, auth=self.get_normal_credentials())
        posted5 = self.post(all_teams, data=new_team3, expect=403, auth=self.get_other_credentials())
        url1 = posted1['url']
        url3 = posted3['url']
        url5 = posted1['url']

        new_team = Team.objects.create(name='newTeam4', organization=Organization.objects.get(pk=2))
        url = '/api/v1/teams/%s/' % new_team.pk

        # can delete teams
        self.delete(url, expect=401)
        self.delete(url, expect=403, auth=self.get_nobody_credentials())
        self.delete(url, expect=403, auth=self.get_other_credentials())        
        self.delete(url, expect=204, auth=self.get_normal_credentials())
        self.delete(url3, expect=204, auth=self.get_super_credentials())

        # =====================================================================
        # ORGANIZATION TEAMS        

        # can list organization teams (filtered by user) -- this is an org admin function
        org_teams = '/api/v1/organizations/2/teams/'
        data1 = self.get(org_teams, expect=401)
        data2 = self.get(org_teams, expect=403, auth=self.get_nobody_credentials())
        data3 = self.get(org_teams, expect=403, auth=self.get_other_credentials())
        data4 = self.get(org_teams, expect=200, auth=self.get_normal_credentials())
        data5 = self.get(org_teams, expect=200, auth=self.get_super_credentials())

        # can add teams to organizations
        new_team1 = dict(name='super new team A')
        # also tests that sub posts overwrite the related field:
        new_team2 = dict(name='super new team B', organization=34567)
        new_team3 = dict(name='super new team C')

        data1 = self.post(org_teams, new_team1, expect=401)
        data1 = self.post(org_teams, new_team1, expect=403, auth=self.get_nobody_credentials())
        data1 = self.post(org_teams, new_team1, expect=403, auth=self.get_other_credentials())
        data2 = self.post(org_teams, new_team2, expect=201, auth=self.get_normal_credentials())
        data3 = self.post(org_teams, new_team3, expect=201, auth=self.get_super_credentials())

        # can remove teams from organizations
        data2['disassociate'] = 1
        url = data2['url']
        deleted = self.post(org_teams, data2, expect=204, auth=self.get_normal_credentials())
        got = self.get(url, expect=404, auth=self.get_normal_credentials())

        # =====================================================================
        # TEAMS USER MEMBERSHIP

        team = Team.objects.filter(organization__pk = 2)[0]
        team_users = '/api/v1/teams/%s/users/' % (team.pk)
        for x in team.users.all():
            team.users.remove(x)
        team.save()

        # can list uses on teams
        self.get(team_users, expect=401)
        self.get(team_users, expect=401, auth=self.get_invalid_credentials())
        self.get(team_users, expect=403, auth=self.get_nobody_credentials())
        self.get(team_users, expect=403, auth=self.get_other_credentials())
        self.get(team_users, expect=200, auth=self.get_normal_credentials())
        self.get(team_users, expect=200, auth=self.get_super_credentials())

        # can add users to teams
        all_users = self.get('/api/v1/users/', expect=200, auth=self.get_super_credentials())
        for x in all_users['results']:
            self.post(team_users, data=x, expect=403, auth=self.get_nobody_credentials())
            self.post(team_users, data=x, expect=204, auth=self.get_normal_credentials())

        self.assertEqual(Team.objects.get(pk=team.pk).users.count(), 4)

        # can remove users from teams
        for x in all_users['results']:
            y = dict(id=x['id'], disassociate=1)
            self.post(team_users, data=y, expect=403, auth=self.get_nobody_credentials())
            self.post(team_users, data=y, expect=204, auth=self.get_normal_credentials())

        self.assertEquals(Team.objects.get(pk=team.pk).users.count(), 0)

        # from a user, can see what teams they are on (related resource)
        print "TEAMS?"
        print User.objects.get(username = 'other').teams.all()

        # from a user, can see what projects they can see based on team association
        # though this resource doesn't do anything else

        # =====================================================================
        # CREDENTIALS

        credentials = '/api/v1/credentials/'
        team_creds = '/api/v1/teams/1/credentials/'
        user_creds = '/api/v1/users/1/credentials/'

        # can add credentials for a team

        # can add credentials for a user

        # can list credentials belonging to a user

        # can list credentials belonging to a team

        # can access all credentials for a user (team+project) in one view

        # ======================================================================
        # PERMISSIONS

        permissions = '/api/v1/permissions/'
        user_permissions = '/api/v1/users/1/permissions/'
        team_permissions = '/api/v1/teams/1/permissions/'

        # can add permissions to a user

        # can add permissions to a team

        # can list permissions

        # can list permissions that match a user

        # can list permissions that match a project

        # can remove permissions


        



