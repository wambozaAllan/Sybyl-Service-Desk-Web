from django.db import models
from django.core.validators import RegexValidator
from phonenumber_field.modelfields import PhoneNumberField

#CompanyDomain
class CompanyDomain(models.Model):
    name = models.CharField(max_length=250)
    description = models.CharField(max_length=255, blank=True)
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)

    def get_companies_count(self):
        return Company.objects.filter(domain=self).count()

    def __str__(self):
        return self.name

#CompanyCategory
class CompanyCategory(models.Model):
    category_value  = models.CharField(max_length=250)
    description     = models.CharField(max_length=255, blank=True)
    created_time    = models.DateTimeField(auto_now_add=True)
    modified_time   = models.DateTimeField(auto_now=True)

    def get_companies_count(self):
        return Company.objects.filter(category=self).count()

    def __str__(self):
        return self.category_value

#Company
class Company(models.Model):
    name            = models.CharField(max_length=100)
    domain          = models.ForeignKey(CompanyDomain, on_delete=models.CASCADE, default=1)
    category        = models.ForeignKey(CompanyCategory, on_delete=models.CASCADE, default=1)
    created_time    = models.DateTimeField(auto_now_add=True)
    modified_time   = models.DateTimeField(auto_now=True)
    logo            = models.ImageField(upload_to='logos', max_length=255, null=True, blank=True)
    owner = models.CharField(max_length=255, blank=True)
    description = models.CharField(max_length=255, blank=True)

    def get_branch_count(self):
        return Branch.objects.filter(company=self).count()

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


# branch_phone_ contact
class BranchPhoneContact(models.Model):
    phone_number = PhoneNumberField()
    secondary_number = PhoneNumberField(blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'branch_phone_contact'


# Department
class Department(models.Model):
    name = models.CharField(max_length=100)
    branch = models.ManyToManyField(Branch)
    company = models.ManyToManyField(Company)
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return reverse('company_management:details_department', kwargs={'pk': self.pk})

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'department'
