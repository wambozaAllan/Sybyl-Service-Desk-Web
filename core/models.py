from django.db import models
from django.utils import timezone

from user_management.models import UserGroup

# SystemModule
# class SystemModule(models.Model):
#     name = models.CharField(max_length=45)

#     class Meta():
#         db_table = 'system_module'

# SystemModuleHasUserGroupPermission
# class SystemModuleHasUserGroupPermission(models.Model):
#     system_module = models.ForeignKey(SystemModule, on_delete=models.DO_NOTHING)
#     usergrouppermission = models.ForeignKey(UserGroupPermission, on_delete=models.DO_NOTHING)

#     class Meta():
#         db_table = 'system_module_has_user_group_permission'

#MODELS FOR MANAGING THE MENU
# class Section(models.Model):
#     name = models.CharField(max_length=100)

#     def __str__(self):
#         return self.name

# class Menu(models.Model):
#     name = models.CharField(max_length=100)
#     section = models.ForeignKey(Section, on_delete=models.CASCADE)

#     def __str__(self):
#         return self.name

# class Submenu(models.Model):
#     name = models.CharField(max_length=100)
#     link = models.CharField(max_length=100)
#     menu = models.ForeignKey(Menu, on_delete=models.CASCADE)

#     def __str__(self):
#         return self.name

class Privilege(models.Model):
    name = models.CharField(max_length=100)
    # submenu = models.ForeignKey(Submenu, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class UsrGrpPermissions(models.Model):
    usergroup = models.ForeignKey(UserGroup, on_delete=models.CASCADE)
    # privilege = models.ForeignKey(Privilege, on_delete=models.CASCADE)

    # def __str__(self):
    #     return self.privilege