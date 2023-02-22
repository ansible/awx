from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from awx.main.models.rbac import Role
from awx.main.models import Organization
from django.apps import apps

# def migrate_org_admin_to_use():
#     user_list = list()
#     member_list = list()
#     for user in User.objects.all():
#         if user.admin_of_organizations:
#             user_list.append(user)
#     for entry in user_list:
#         membership = entry.admin_of_organizations
#         member_list.append({'user_id': entry.id, 'org_queryset': membership})
#     for orgs in Organization.objects.filter(name__in=membership.name):
#         print(orgs)
# def migrate_org_admin_to_use():
#     user_list = list()
#     for user in User.objects.all():
#         if user.admin_of_organizations:
#             user_list.append(user)
#     member_list = list()
#     for entry in user_list:
#         membership = entry.admin_of_organizations
#         member_list.append(membership)
#     org_list = list()
#     for orgs in member_list:
#         for org_name in orgs:
#             org_list.append(org_name.id)
#     ins_list = list()
#     ins = Organization.objects.filter(id__in=org_list)
#     for org in ins:
#         igs = org.instance_groups.all()
#         if not igs:
#             continue
#         else:
#             ins_list.append(igs)
#     for instance in ins_list:
#         for inst in instance:
#             for user in user_list:
#                 if user.admin_of_organizations in ins_list:
#                     inst.use_role.members.add(user_list)
def migrate_org_admin_to_use():
          user_list = list()
          for user in User.objects.all():
              if user.admin_of_organizations:
                  user_list.append(user)
          member_list = list()
          for entry in user_list:
              membership = entry.admin_of_organizations
              member_list.append(membership)
          org_list = list()
          for orgs in member_list:
              for org_name in orgs:
                  org_list.append(org_name.id)
          ins_list = list()
          ins = Organization.objects.filter(id__in=org_list)
          for org in ins:
              igs = org.instance_groups.all()
              if not igs:
                  continue
              else:
                  ins_list.append(igs)
          for instance in ins_list:
              for inst in instance:
                  for user in user_list:
                      for org in ins:
                          if user in org.admin_role.members.all():
                              inst.use_role.members.add(user)
migrate_org_admin_to_use()


            

