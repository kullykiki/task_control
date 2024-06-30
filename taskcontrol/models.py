from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta

class Country(models.Model):
    name_th =  models.CharField(max_length=255, default=None, null=True, blank=True)
    name_en =  models.CharField(max_length=255, default=None, null=True, blank=True)

    class Meta:
        db_table = 'country'

class Geography(models.Model):
    name_th =  models.CharField(max_length=255, default=None, null=True, blank=True)
    name_en =  models.CharField(max_length=255, default=None, null=True, blank=True)

    class Meta:
        db_table = 'geography'

class AddressBase(models.Model):
    address = models.CharField(max_length=255, default=None, null=True, blank=True)
    address2 = models.CharField(max_length=255, default=None, null=True, blank=True)
    province = models.ForeignKey('Province', on_delete=models.CASCADE, blank=True, null=True)
    district = models.ForeignKey('District', on_delete=models.CASCADE, blank=True, null=True)
    subdistrict = models.ForeignKey('Subdistrict', on_delete=models.CASCADE, blank=True, null=True)
    client = models.ForeignKey('Client', on_delete=models.CASCADE, blank=True, null=True, related_name='client_addressbase')
    contact = models.ForeignKey('Contact', on_delete=models.CASCADE, blank=True, null=True, related_name='contact_addressbase')
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='address_create_by')
    create_at = models.DateTimeField(default=timezone.now)
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='address_update_by')
    update_at = models.DateTimeField(default=timezone.now)
    voide_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='address_voide_by')
    voide_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'address_base'

class Client(models.Model):
    code = models.CharField(max_length=255, unique=True, default=None, null=True, blank=True)
    company_name = models.CharField(max_length=255, default=None, null=True, blank=True)
    tax_id = models.CharField(max_length=255, default=None, null=True, blank=True)
    create_client_date = models.DateField(blank=True, null=True)
    channel = models.ForeignKey('Channel', on_delete=models.CASCADE, blank=True, null=True, related_name='client_channel')
    detail = models.CharField(max_length=255, default=None, null=True, blank=True)
    contact = models.ForeignKey('Contact', on_delete=models.CASCADE, blank=True, null=True, related_name='client_contact')
    status = models.BooleanField(default=False)
    register_tax = models.ForeignKey('RegisterTax', on_delete=models.CASCADE, blank=True, null=True, related_name='client_register_tax')
    company_address = models.ForeignKey(AddressBase, on_delete=models.CASCADE, blank=True, null=True, related_name='client_company_address')
    file = models.ForeignKey('FileManage', on_delete=models.CASCADE, blank=True, null=True, related_name='client_file')
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='client_create_by')
    create_at = models.DateTimeField(default=timezone.now)
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='client_update_by')
    update_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'client'

class FileManage(models.Model):
    client = models.ForeignKey('Client', on_delete=models.CASCADE, blank=True, null=True)
    file_client = models.FileField(upload_to='client_files/', blank=True, null=True)
    image_client = models.ImageField(upload_to='client_images/', blank=True, null=True)
    engagement = models.ForeignKey('Engagement', on_delete=models.CASCADE, blank=True, null=True)
    file_engagement = models.FileField(upload_to='engagement_files/', blank=True, null=True)
    image_engagement = models.ImageField(upload_to='engagement_images/', blank=True, null=True)
    task = models.ForeignKey('Task', on_delete=models.CASCADE, blank=True, null=True)
    file_task = models.FileField(upload_to='task_files/', blank=True, null=True)
    image_task = models.ImageField(upload_to='task_images/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='file_create_by')
    create_at = models.DateTimeField(default=timezone.now)
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='file_update_by')
    update_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'file_manage'

class Province(models.Model):
    name_th =  models.CharField(max_length=255, default=None, null=True, blank=True)
    name_en =  models.CharField(max_length=255, default=None, null=True, blank=True)
    geography = models.ForeignKey(Geography, on_delete=models.CASCADE, blank=True, null=True, related_name='provinces')
    country = models.ForeignKey(Country, on_delete=models.CASCADE, blank=True, null=True, related_name='provinces')

    class Meta:
        db_table = 'province'

class District(models.Model):
    name_th =  models.CharField(max_length=255, default=None, null=True, blank=True)
    name_en =  models.CharField(max_length=255, default=None, null=True, blank=True)
    province = models.ForeignKey(Province, on_delete=models.CASCADE, blank=True, null=True, related_name='districts')

    class Meta:
        db_table = 'district'

class Subdistrict(models.Model):
    name_th =  models.CharField(max_length=255, default=None, null=True, blank=True)
    name_en =  models.CharField(max_length=255, default=None, null=True, blank=True)
    zipcode = models.PositiveIntegerField()
    district = models.ForeignKey(District, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        db_table = 'subdistrict'

class RegisterTax(models.Model):
    vat = models.BooleanField(default=False)
    vat_date = models.DateField(blank=True, null=True)
    sbt = models.BooleanField(default=False)
    sbt_date = models.DateField(blank=True, null=True)
    sso = models.BooleanField(default=False)
    sso_date = models.DateField(blank=True, null=True)
    dbd_e_filling = models.BooleanField(default=False)
    dbd_e_filling_date = models.DateField(blank=True, null=True)
    company = models.BooleanField(default=False)
    company_date = models.DateField(blank=True, null=True)
    company_period_date = models.DateField(blank=True, null=True)
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='register_tax_create_by')
    create_at = models.DateTimeField(default=timezone.now)
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='register_tax_update_by')
    update_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'register_tax'

class RegisterType(models.Model):
    short_name = models.CharField(max_length=255, default=None, null=True, blank=True)
    name_th =  models.CharField(max_length=255, default=None, null=True, blank=True)
    name_en =  models.CharField(max_length=255, default=None, null=True, blank=True)
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='register_type_create_by')
    create_at = models.DateTimeField(default=timezone.now)
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='register_type_update_by')
    update_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'register_type'

class Channel(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'channel'

class Contact(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='contact_client')
    name = models.CharField(max_length=255, default=None, null=True, blank=True)
    position = models.CharField(max_length=255, default=None, null=True, blank=True)
    phone = models.CharField(max_length=255, default=None, null=True, blank=True)
    email = models.EmailField(default=None, null=True, blank=True)
    line = models.CharField(max_length=255, default=None, null=True, blank=True)
    other = models.CharField(max_length=255, default=None, null=True, blank=True)
    address = models.ForeignKey(AddressBase, on_delete=models.CASCADE, blank=True, null=True, related_name='contact_address')
    address2 = models.ForeignKey(AddressBase, on_delete=models.CASCADE, blank=True, null=True, related_name='company_address')
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='contact_create_by')
    create_at = models.DateTimeField(default=timezone.now)
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='contact_update_by')
    update_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'contact'

class ClientPassword(models.Model):
    client = models.ForeignKey('Client', null=True, blank=True, on_delete=models.CASCADE)
    type_password = models.ForeignKey('RegisterType', null=True, blank=True, on_delete=models.CASCADE)
    username =  models.CharField(max_length=255, default=None, null=True, blank=True)
    password = models.TextField(default=None, null=True, blank=True)
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='client_password_create_by')
    create_at = models.DateTimeField(default=timezone.now)
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='client_password_update_by')
    update_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'client_password'

class Engagement(models.Model):
    client = models.ForeignKey('Client', on_delete=models.CASCADE)
    job_code = models.CharField(max_length=255, unique=True)
    start_date_service = models.DateField()
    end_date_service = models.DateField()
    start_date_period = models.DateField()
    end_date_period = models.DateField(null=True, blank=True)
    end_date_period_infinity = models.BooleanField(default=False)
    service_fee = models.DecimalField(max_digits=16, decimal_places=2, blank=True, null=True)
    administrator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='admin_engagements', null=True, blank=True)
    administrator_date = models.DateTimeField(null=True, blank=True)
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='approver_engagements', null=True, blank=True)
    approved_date = models.DateTimeField(null=True, blank=True)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviewer_engagements', null=True, blank=True)
    review_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=255, default=None, null=True, blank=True)
    file = models.ForeignKey('FileManage', on_delete=models.CASCADE, related_name='engagement_file', null=True, blank=True)
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='engagement_create_by')
    create_at = models.DateTimeField(default=timezone.now)
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='engagement_update_by')
    update_at = models.DateTimeField(default=timezone.now)
    category = models.ForeignKey('EngagementCategory', on_delete=models.CASCADE, related_name='engagement_category', null=True, blank=True)
    type = models.ForeignKey('EngagementType', on_delete=models.CASCADE, related_name='engagement_type', null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='engagement_create_by')
    create_at = models.DateTimeField(default=timezone.now)
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='engagement_update_by')
    update_at = models.DateTimeField(default=timezone.now)
    completed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='engagement_completed_by')
    completed_at = models.DateTimeField(blank=True, null=True)
    voide_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='engagement_voide_by')
    voide_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'engagement'

    def update_status(self):
        open_jobs = self.task_set.filter(status='OPEN_JOB').count()
        in_progress = self.task_set.filter(status='IN_PROGRESS').count()
        review = self.task_set.filter(status='REVIEW').count()
        pending_client = self.task_set.filter(status='PENDING_CLIENT').count()
        done = self.task_set.filter(status='DONE').count()

        # ตรวจสอบสถานะของ EngagementDetail
        all_details_done = self.engagementdetail_set.filter(status='DONE').count() == self.engagementdetail_set.count()

        # ตรวจสอบว่ามี EngagementDetail ทุกตัวเป็นสถานะ DONE หรือไม่
        if all_details_done:
            self.status = 'DONE'
        elif open_jobs > 0:
            self.status = 'OPEN_JOB'
        elif pending_client > 0:
            self.status = 'PENDING_CLIENT'
        elif review > 0:
            self.status = 'REVIEW'
        elif in_progress > 0:
            self.status = 'IN_PROGRESS'
        else:
            self.status = 'OPEN_JOB'
        self.save()

class EngagementDetail(models.Model):
    engagement = models.ForeignKey(Engagement, on_delete=models.CASCADE)
    engagement_category = models.ForeignKey('EngagementCategory', on_delete=models.CASCADE, related_name='engagement_detail_category', null=True, blank=True)
    engagement_type = models.ForeignKey('EngagementType', on_delete=models.CASCADE, related_name='engagement_detail_type', null=True, blank=True)
    type = models.CharField(max_length=255, default=None, null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    notification = models.CharField(max_length=255, default=None, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    review_by = models.BooleanField(default=False)
    approved_by = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='OPEN_JOB')
    comment = models.TextField(blank=True, null=True)
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='engagement_detail_create_by')
    create_at = models.DateTimeField(default=timezone.now)
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='engagement_detail_update_by')
    update_at = models.DateTimeField(default=timezone.now)
    completed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='engagement_detail_completed_by')
    completed_at = models.DateTimeField(blank=True, null=True)
    voide_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='engagement_detail_voide_by')
    voide_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'engagement_detail'

    def update_status(self):
        # นับจำนวนงานในแต่ละสถานะที่เกี่ยวข้องกับ EngagementDetail ที่เกี่ยวข้อง
        open_jobs = EngagementDetail.objects.filter(engagement=self.engagement, status='OPEN_JOB').count()
        in_progress = EngagementDetail.objects.filter(engagement=self.engagement, status='IN_PROGRESS').count()
        review = EngagementDetail.objects.filter(engagement=self.engagement, status='REVIEW').count()
        pending_client = EngagementDetail.objects.filter(engagement=self.engagement, status='PENDING_CLIENT').count()
        done = EngagementDetail.objects.filter(engagement=self.engagement, status='DONE').count()

        # อัพเดทสถานะของ EngagementDetail
        if done > 0:
            self.status = 'DONE'
            if not self.completed_at:
                self.completed_at = timezone.now()
        elif open_jobs > 0:
            self.status = 'OPEN_JOB'
        elif pending_client > 0:
            self.status = 'PENDING_CLIENT'
        elif review > 0:
            self.status = 'REVIEW'
        elif in_progress > 0:
            self.status = 'IN_PROGRESS'
        else:
            self.status = 'OPEN_JOB'

        self.save()

class EngagementCategory(models.Model):
    name_th = models.CharField(max_length=255, default=None, null=True, blank=True)
    name_en = models.CharField(max_length=255, default=None, null=True, blank=True)
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='engagement_category_create_by')
    create_at = models.DateTimeField(default=timezone.now)
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='engagement_category_update_by')
    update_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'engagement_category'
class EngagementType(models.Model):
    name_th = models.CharField(max_length=255, default=None, null=True, blank=True)
    name_en = models.CharField(max_length=255, default=None, null=True, blank=True)
    description = models.CharField(max_length=255, default=None, null=True, blank=True)
    category = models.ForeignKey(EngagementCategory, on_delete=models.CASCADE)
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='engagement_type_create_by')
    create_at = models.DateTimeField(default=timezone.now)
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='engagement_type_update_by')
    update_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'engagement_type'

class Task(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)
    number = models.CharField(max_length=255, null=True, blank=True, unique=True)
    new_job = models.CharField(max_length=255, null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    comment = models.TextField(blank=True, null=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, default='OPEN_JOB')
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='task_create_by')
    create_at = models.DateTimeField(default=timezone.now)
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='task_update_by')
    update_at = models.DateTimeField(default=timezone.now)
    completed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='task_completed_by')
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'task'

    def update_status(self):
        # นับจำนวนงานในแต่ละสถานะ
        open_jobs = Task.objects.filter(status='OPEN_JOB').count()
        in_progress = Task.objects.filter(status='IN_PROGRESS').count()
        review = Task.objects.filter(status='REVIEW').count()
        pending_client = Task.objects.filter(status='PENDING_CLIENT').count()
        done = Task.objects.filter(status='DONE').count()

        # อัพเดทสถานะของงาน Task
        if done > 0:
            self.status = 'DONE'
            if not self.completed_at:
                self.completed_at = timezone.now()
        elif open_jobs > 0:
            self.status = 'OPEN_JOB'
        elif pending_client > 0:
            self.status = 'PENDING_CLIENT'
        elif review > 0:
            self.status = 'REVIEW'
        elif in_progress > 0:
            self.status = 'IN_PROGRESS'
        else:
            self.status = 'OPEN_JOB'
        self.save()

