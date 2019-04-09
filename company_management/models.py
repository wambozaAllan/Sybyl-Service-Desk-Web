from django.db import models

#CompanyCategory
class CompanyCategory(models.Model):
    CATEGORY_CHOICES = (('Self', 'Self'),('Client', 'Client'),('Vendor', 'Vendor'),('Partner', 'Partner'),)
    category_value = models.CharField(max_length=8,choices=CATEGORY_CHOICES,default='Client',)
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.category_value

    class Meta():
        db_table = 'company_category'

#Company
class Company(models.Model):
    name            = models.CharField(max_length=100)
    category        = models.ForeignKey(CompanyCategory, on_delete=models.CASCADE, default=1)
    created_time    = models.DateTimeField(auto_now_add=True)
    modified_time   = models.DateTimeField(auto_now=True)
    logo            = models.ImageField(upload_to='logos', max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta():
        db_table = 'company'


class Branch(models.Model):
    name = models.CharField(max_length=100)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    location = models.CharField(max_length=100)
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'branch'

# branch_contact
class BranchContact(models.Model):
    contact_type = models.CharField(max_length=45)
    contact_value = models.CharField(max_length=45)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'branch_contact'

# Department
class Department(models.Model):
    name = models.CharField(max_length=100)
    branch = models.ManyToManyField(Branch)
    company = models.ManyToManyField(Company)
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return reverse('company_management:detailsDepartment', kwargs={'pk': self.pk})

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'department'
