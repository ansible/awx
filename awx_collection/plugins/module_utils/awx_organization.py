#!/usr/bin/python
from .awx_request import get_awx_resources

def get_team_members(team, awx_auth):
    members = get_awx_resources(uri='/api/v2/teams/' + str(team['id']) + '/users/', previousPageResults=[], awx_auth=awx_auth)
    users = []
    members_info_set = set()

    for member in members:
        users.append(member['username'])
        member_info = {member['username'] + ';' + member['first_name'] + ';' + member['last_name'] + ';' + member['email']}
        members_info_set.update(member_info)

    exported_team = {'name': team['name'], 'description': team['description'], 'users': users}
    return exported_team, members_info_set

def get_organization_teams(organization, awx_auth):
    users_info_set = set()
    exported_teams = []

    teams = get_awx_resources(uri='/api/v2/teams/?organization=' + str(organization['id']), previousPageResults=[], awx_auth=awx_auth)
    for team in teams:
        team, members_info_set = get_team_members(team, awx_auth)
        exported_teams.append(team)
        users_info_set.update(members_info_set)
    return teams, users_info_set

def get_role_members(role, awx_auth):
    members = get_awx_resources(uri='/api/v2/roles/' + str(role['id']) + '/users/', previousPageResults=[], awx_auth=awx_auth)
    users = []
    members_info_set = set()

    for member in members:
        users.append(member['username'])
        member_info = {member['username'] + ';' + member['first_name'] + ';' + member['last_name'] + ';' + member['email']}
        members_info_set.update(member_info)

    teams = get_awx_resources(uri='/api/v2/roles/' + str(role['id']) + '/teams/', previousPageResults=[], awx_auth=awx_auth)
    team_names = [team['name'] for team in teams]

    exported_role = {'name': role['name'], 'users': users, 'teams': team_names}
    return exported_role, members_info_set

def get_organization_roles(organization, awx_auth):
    users_info_set = set()
    exported_roles = []
    roles = get_awx_resources(uri='/api/v2/organizations/' + str(organization['id']) + '/object_roles/', previousPageResults=[], awx_auth=awx_auth)

    for role in roles:
        role, members_info_set = get_role_members(role, awx_auth)
        exported_roles.append(role)
        users_info_set.update(members_info_set)

    return exported_roles, users_info_set