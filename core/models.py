from django.db import models
from django.utils import timezone


# SystemModule
# class SystemModule(models.Model):
#     name = models.CharField(max_length=45)

#     class Meta():
#         db_table = 'system_module'


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
