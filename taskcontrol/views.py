from django.shortcuts import render, redirect, get_object_or_404
from taskcontrol.models import *
from .forms import CustomUserCreationForm, CustomPasswordResetForm
from datetime import datetime, date, timedelta
from django.utils import timezone
from django.contrib import messages
from django.db import transaction
from django.utils.dateparse import parse_date
from django.http import JsonResponse, HttpResponse, Http404, HttpResponseBadRequest, HttpResponseNotFound
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.db.models import Max, Count, F, Subquery, Q, Case, When, Value, CharField, Prefetch
from django.core.paginator import Paginator
from django.core.exceptions import ObjectDoesNotExist
from collections import Counter
from django.views.decorators.http import require_POST
from dateutil.relativedelta import relativedelta
from django.views.decorators.csrf import csrf_exempt
from django.db.models.functions import ExtractMonth, ExtractYear
import json


# Constants
STATUS_OPEN_JOB = ('OPEN_JOB', 'PENDING_CLIENT', 'REVIEW', 'IN_PROGRESS')
STATUS_DONE = ('DONE',)

#TODO Error404
def error_404_view(request, exception):
    return render(request, 'task/eror404.html', status=404)

#TODO Coding
def building_code(request):
    return render(request, 'task/coding.html')

#TODO Login
def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'เข้าสู่ระบบสำเร็จ')
            return redirect('taskcontrol:dashboard')
        else:
            messages.error(request, 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')
    return render(request, 'accounts/login.html')

#TODO Logout
def logout_view(request):
    if request.user.is_authenticated:
        # last_login_time = request.user.last_login
        logout(request)
        messages.success(request, 'ออกจากระบบเรียบร้อย.')

        # if last_login_time is not None:
        #     current_time = datetime.now()
        #     time_difference = current_time - last_login_time

        #     if time_difference.total_seconds() > 3600:
        #         messages.success(request, 'ออกจากระบบ เนื่องจากไม่มีการใช้งานเกิน 1 ชั่วโมง.')
    return redirect('taskcontrol:login')

#TODO Others
def parse_date(date_string):
    if not date_string:
        return None
    try:
        return datetime.strptime(date_string, "%Y-%m-%d")
    except ValueError:
        print(f"Error parsing date string: {date_string}")
        return None

#TODO GetData
def get_districts(request):
    province_id = request.GET.get('province_id')
    district = District.objects.filter(province=province_id).all().values('id','name_th')
    return JsonResponse(list(district),safe=False)

def get_subdistricts(request):
    district_id = request.GET.get('district_id')
    subdistrict = Subdistrict.objects.filter(district=district_id).all().values('id', 'name_th', 'zipcode')
    return JsonResponse(list(subdistrict),safe=False)

def get_channel(request):
    channel_id = request.GET.get('channel_id')
    channel = Channel.objects.filter(id=channel_id).values('id', 'name')
    return JsonResponse(list(channel), safe=False)

def gen_engagement_code_auto(request):
    latest_job_code = Engagement.objects.aggregate(Max('job_code'))['job_code__max']

    # ตรวจสอบหาก latest_job_code เป็น None แล้วกำหนดให้เป็น '24-0001'
    if latest_job_code is not None:
        current_number = int(latest_job_code.split('-')[1]) + 1
    else:
        current_number = 1

    # ดึงปีปัจจุบัน
    current_year = datetime.now().year

    new_job_code = f'24-{current_number:04d}'

    return JsonResponse({'latest_job_code': new_job_code})

#TODO Client
@login_required
def client_list(request):
    clients_list = Client.objects.all().order_by('code')

    contacts = []
    for client in clients_list:
        first_contact = Contact.objects.filter(client_id=client.id).first()
        contacts.append(first_contact)

    return render(request, 'task/clients/client_list.html', {
        'clients_list': clients_list,
        'contacts': contacts,
    })

#TODO Record Client
@login_required
def record_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    engagement_all = Engagement.objects.filter(client_id=client_id).all()
    contact_all = Contact.objects.filter(client_id=client_id).all()
    return render(request, 'task/clients/record_client.html', {
        'client': client,
        'engagement_all':engagement_all,
        'contact_all':contact_all
    })

#TODO Client Detail
@login_required
def client_detail(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    engagements = Engagement.objects.filter(client_id=client_id).exclude(status='DONE').order_by('job_code')

    unique_engagements = []
    seen_job_codes = set()
    for engagement in engagements:
        if engagement.job_code not in seen_job_codes:
            unique_engagements.append(engagement)
            seen_job_codes.add(engagement.job_code)

    # Collect unique engagement types for each unique engagement
    engagement_data = []
    for engagement in unique_engagements:
        engagement_types = EngagementDetail.objects.filter(engagement=engagement).exclude(engagement__status='DONE').values_list('engagement_type__name_th', flat=True).distinct()
        engagement_data.append({
            'engagement': engagement,
            'types': list(set(engagement_types))  # Remove duplicates
        })

    contact_all = Contact.objects.filter(client_id=client_id)
    contacts = Contact.objects.all()
    subdistricts = Subdistrict.objects.values('id', 'name_th', 'zipcode')
    districts = District.objects.values('id', 'name_th')
    provinces = Province.objects.all().order_by('name_th')
    register_types = RegisterType.objects.values('id', 'short_name', 'name_th', 'name_en')
    channels = Channel.objects.values('id', 'name')

    context = {
        'client': client,
        'engagement_data': engagement_data,
        'contact_all': contact_all,
        'contacts': contacts,
        'subdistricts': subdistricts,
        'districts': districts,
        'provinces': provinces,
        'register_types': register_types,
        'channels': channels,
    }
    return render(request, 'task/clients/client_detail.html', context)

#TODO Client Create
@login_required
def client_create(request):
    register_tax = None
    file = None
    contact = None
    client = None

    subdistrict = Subdistrict.objects.values('id', 'name_th', 'zipcode')
    district = District.objects.values('id', 'name_th')
    province = Province.objects.values('id', 'name_th').order_by('name_th')
    register_types = RegisterType.objects.values('id','short_name','name_th','name_en')
    channels = Channel.objects.values('id','name')

    if request.method == 'POST':
        c_code = request.POST.get('c_code', '')
        c_company_name = request.POST.get('c_company_name', '')
        c_tax_id = request.POST.get('c_tax_id', '')
        c_address = request.POST.get('c_address')
        c_address2 = request.POST.get('c_address2')
        c_province = request.POST.get('c_province')
        c_district = request.POST.get('c_district')
        c_subdistrict = request.POST.get('c_subdistrict')
        c_channel = request.POST.get('c_channel')
        c_detail = request.POST.get('c_detail')
        c_status = request.POST.get('c_status')
        c_status = True if c_status == 'on' else False
        c_create_client_date = request.POST.get('c_create_client_date', '')

        r_company = request.POST.get('r_company') == 'True'
        r_company_date = request.POST.get('r_company_date')
        r_company_period_date = request.POST.get('r_company_period_date')
        r_vat = request.POST.get('r_vat') == 'True'
        r_vat_date = request.POST.get('r_vat_date')
        r_sbt = request.POST.get('r_sbt') == 'True'
        r_sbt_date = request.POST.get('r_sbt_date')
        r_sso = request.POST.get('r_sso') == 'True'
        r_sso_date = request.POST.get('r_sso_date')
        r_dbd_e_filling = request.POST.get('r_dbd_e_filling') == 'True'
        r_dbd_e_filling_date = request.POST.get('r_dbd_e_filling_date')
        
        date_c_create_client_date = parse_date(c_create_client_date)

        c_r_company_date = parse_date(r_company_date)
        c_r_company_period_date = parse_date(r_company_period_date)
        c_r_vat_date = parse_date(r_vat_date)
        c_r_sbt_date = parse_date(r_sbt_date)
        c_r_sso_date = parse_date(r_sso_date)
        c_r_dbd_e_filling_date = parse_date(r_dbd_e_filling_date)

        company_address = AddressBase(
            address = c_address,
            address2 = c_address2,
            province=Province.objects.filter(id=c_province).first(),
            district=District.objects.filter(id=c_district).first(),
            subdistrict=Subdistrict.objects.filter(id=c_subdistrict).first(),
        )
        company_address.save()

        client = Client(
            code=c_code,
            company_name=c_company_name,
            tax_id=c_tax_id,
            create_client_date = date_c_create_client_date,
            channel=Channel.objects.filter(id=c_channel).first(),
            detail=c_detail,
            status=c_status,
            register_tax=register_tax,
            company_address = company_address,
            create_by=request.user,
        )
        client.save()

        register_tax = RegisterTax(
            vat=r_vat,
            vat_date=c_r_vat_date,
            sbt=r_sbt,
            sbt_date=c_r_sbt_date,
            sso=r_sso,
            sso_date=c_r_sso_date,
            dbd_e_filling=r_dbd_e_filling,
            dbd_e_filling_date=c_r_dbd_e_filling_date,
            company=r_company,
            company_date=c_r_company_date,
            company_period_date=c_r_company_period_date,
        )
        register_tax.save()

        company_address.client = client
        company_address.save()

        client.file = file
        client.contact = contact
        client.register_tax = register_tax
        client.save()

        success_message = 'บันทึกข้อมูลลูกค้าเรียบร้อยแล้ว'
        messages.success(request, success_message)

        return redirect('taskcontrol:record_client', client_id=client.id)

    return render(request, 'task/clients/client_create.html', {
        'client' : client,
        'subdistrict': subdistrict,
        'district': district,
        'province': province,
        'register_types': register_types,
        'channels' : channels,
    })

#TODO Client Update
@login_required
def client_update(request, client_id):
    client = get_object_or_404(Client, id=client_id)

    if request.method == 'POST':
        # Extract data from the POST request
        update_c_code = request.POST.get('update_c_code', '')
        update_c_company_name = request.POST.get('update_c_company_name', '')
        update_c_tax_id = request.POST.get('update_c_tax_id', '')
        update_c_address = request.POST.get('update_c_address', '')
        update_c_address2 = request.POST.get('update_c_address2', '')
        update_c_province_id = request.POST.get('update_c_province', '')
        update_c_district_id = request.POST.get('update_c_district', '')
        update_c_subdistrict_id = request.POST.get('update_c_subdistrict', '')
        update_c_channel_id = request.POST.get('update_c_channel', '')
        update_c_detail = request.POST.get('update_c_detail', '')
        update_c_status = request.POST.get('update_c_status') == 'on'
        update_r_company = request.POST.get('update_r_company', '') == 'True'
        update_r_company_date = request.POST.get('update_r_company_date')
        update_r_company_period_date = request.POST.get('update_r_company_period_date')
        update_r_vat = request.POST.get('update_r_vat', '') == 'True'
        update_r_vat_date = request.POST.get('update_r_vat_date')
        update_r_sbt = request.POST.get('update_r_sbt', '') == 'True'
        update_r_sbt_date = request.POST.get('update_r_sbt_date')
        update_r_sso = request.POST.get('update_r_sso', '') == 'True'
        update_r_sso_date = request.POST.get('update_r_sso_date')
        update_r_dbd_e_filling = request.POST.get('update_r_dbd_e_filling', '') == 'True'
        update_r_dbd_e_filling_date = request.POST.get('update_r_dbd_e_filling_date')

        # Parse dates
        update_date_vat = parse_date(update_r_vat_date)
        update_date_sbt = parse_date(update_r_sbt_date)
        update_date_sso = parse_date(update_r_sso_date)
        update_date_dbd_e_filling = parse_date(update_r_dbd_e_filling_date)
        update_date_company_date = parse_date(update_r_company_date)

        province_instance = Province.objects.get(id=update_c_province_id)

        # Update or create address
        update_company_address, _ = AddressBase.objects.update_or_create(
            id=client.company_address.id,
            defaults={
                'address': update_c_address,
                'address2': update_c_address2,
                'province_id': province_instance.id,
                'district_id': update_c_district_id,
                'subdistrict_id': update_c_subdistrict_id,
            }
        )

        # Update or create register tax
        update_register_tax, _ = RegisterTax.objects.update_or_create(
            id=client.register_tax.id,
            defaults={
                'vat': update_r_vat,
                'vat_date': update_date_vat,
                'sbt': update_r_sbt,
                'sbt_date': update_date_sbt,
                'sso': update_r_sso,
                'sso_date': update_date_sso,
                'dbd_e_filling': update_r_dbd_e_filling,
                'dbd_e_filling_date': update_date_dbd_e_filling,
                'company': update_r_company,
                'company_date': update_date_company_date,
                'company_period_date': update_r_company_period_date,
            }
        )

        update_channel = None
        if update_c_channel_id:
            try:
                update_channel = Channel.objects.get(id=update_c_channel_id)
            except Channel.DoesNotExist:
                pass

        # Update client details
        client.code = update_c_code
        client.company_name = update_c_company_name
        client.tax_id = update_c_tax_id
        client.channel = update_channel  # Assign the retrieved Channel instance
        client.detail = update_c_detail
        client.status = update_c_status
        client.company_address = update_company_address
        client.register_tax = update_register_tax
        client.save()

        return redirect('taskcontrol:client_detail', client_id=client.id)

    return render(request, 'task/clients/client_detail.html', {
        'client': client,
    })

#TODO Client Deleted
@login_required
@require_POST
def client_delete(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    client.delete()
    return JsonResponse({'status': 'success'})

#TODO Contact
@login_required
def create_contact(request, client_id):
    subdistricts = Subdistrict.objects.values('id', 'name_th', 'zipcode')
    districts = District.objects.values('id', 'name_th')
    provinces = Province.objects.values('id', 'name_th').order_by('name_th')
    contacts = Contact.objects.filter(client=client_id)
    client = get_object_or_404(Client, id=client_id)
    company_address = client.company_address
    error_message = None

    if request.method == 'POST':
        ct_name = request.POST.get('ct_name')
        ct_position = request.POST.get('ct_position')
        ct_phone = request.POST.get('ct_phone')
        ct_email = request.POST.get('ct_email')
        ct_line = request.POST.get('ct_line')
        ct_other = request.POST.get('ct_other')
        ct_address = request.POST.get('ct_address')
        ct_address2 = request.POST.get('ct_address2')
        ct_province = request.POST.get('ct_province')
        ct_district = request.POST.get('ct_district')
        ct_subdistrict = request.POST.get('ct_subdistrict')
        same_as_company = request.POST.get('same_as_company') == 'on'

        # Determine contact address
        if same_as_company:
            if company_address:
                ct_address2 = company_address.address2
                contact_address = AddressBase(
                    address2=ct_address2,
                )
                contact_address.save()

                contact = Contact(
                    client=client,
                    name=ct_name,
                    position=ct_position,
                    phone=ct_phone,
                    email=ct_email,
                    line=ct_line,
                    other=ct_other,
                    address=contact_address,
                )
                contact.save()

                client.contact = contact
                client.save()

                return redirect('taskcontrol:create_contact', client_id=contact.client_id)
            else:
                error_message = 'Company address not found. Please fill in the contact address manually.'
        else:
            contact_address = AddressBase(
                address=ct_address,
                address2=ct_address2,
                province=Province.objects.filter(id=ct_province).first(),
                district=District.objects.filter(id=ct_district).first(),
                subdistrict=Subdistrict.objects.filter(id=ct_subdistrict).first(),
            )
            contact_address.save()

            contact = Contact(
                client=client,
                name=ct_name,
                position=ct_position,
                phone=ct_phone,
                email=ct_email,
                line=ct_line,
                other=ct_other,
                address=contact_address,
            )
            contact.save()

            return redirect('taskcontrol:create_contact', client_id=contact.client_id)
    
    return render(request, 'task/clients/client_contact.html', {
        'client_id': client_id,
        'subdistricts': subdistricts,
        'districts': districts,
        'provinces': provinces,
        'client': client,
        'company_address': company_address,
        'contacts': contacts,
        'error_message': error_message,  # Pass the error message to the template
    })

#TODO Contact Deleted
@login_required
def delete_contact(request, contact_id):
    contact = get_object_or_404(Contact, pk=contact_id)
    contact.delete()
    return JsonResponse({'message': 'Contact deleted successfully'})

#TODO Password
@login_required
def password_list(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    register_types = RegisterType.objects.all()
    client_passwords = ClientPassword.objects.filter(client=client)
    return render(request, 'task/clients/client_password.html', {'client': client, 'register_types': register_types, 'client_passwords': client_passwords})

#TODO Password Client
@login_required
def create_password(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    register_types = RegisterType.objects.all()
    passwords = ClientPassword.objects.filter(client=client)

    if request.method == 'POST':
        type_password_id = request.POST.get('type_password')
        username = request.POST.get('username')
        password_value = request.POST.get('password')

        type_password = get_object_or_404(RegisterType, id=type_password_id)

        password = ClientPassword.objects.create(
            type_password=type_password,
            username=username,
            password=password_value,
            client=client,
            create_by=request.user
        )
        return redirect('taskcontrol:create_password', client_id=client.id)
    return render(request, 'task/clients/client_password.html', {'register_types': register_types, 'client': client, 'passwords': passwords})

#TODO Password Update
@login_required
def update_password(request, password_id):
    password = get_object_or_404(ClientPassword, id=password_id)
    register_types = RegisterType.objects.all()
    
    if request.method == 'POST':
        edit_type_password = request.POST.get('edit_type_password')
        edit_username = request.POST.get('edit_username')
        edit_password = request.POST.get('edit_password')
        
        type_password = get_object_or_404(RegisterType, id=edit_type_password)

        password.type_password = type_password
        password.username = edit_username
        password.password = edit_password
        password.update_by = request.user
        password.save()
        
        return redirect('taskcontrol:create_password', client_id=password.client.id)

    return render(request, 'task/clients/client_password.html', {
        'register_types': register_types,
        'password': password,
    })

#TODO Password Deleted
@login_required
def delete_password(request, password_id):
    password_instance = get_object_or_404(ClientPassword, id=password_id)

    if request.method == 'POST':
        password_instance.delete()
        return redirect('taskcontrol:password_list', client_id=password_instance.client.id)
    
#TODO File Client
@login_required
def file_client_list(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    files = FileManage.objects.filter(client_id=client_id).all()
    return render(request, 'task/clients/client_file.html', {'client': client, 'files': files})

#TODO File Client Create
@login_required
def file_client_create(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    files = FileManage.objects.filter(client=client)

    if request.method == 'POST':
        c_file = request.FILES.get('c_file')
        c_description = request.POST.get('c_description')
        c_image = request.FILES.get('c_image')

        user = request.user
        file = FileManage(
            file_client=c_file,
            description=c_description,
            image_client=c_image,
            client=client,
            create_by=user,
        )
        file.save()
        return redirect('taskcontrol:file_client_create', client_id=client.id)

    return render(request, 'task/clients/client_file.html', {'client': client, 'files': files})

#TODO File Client Deleted
@login_required
@require_POST
def file_client_delete(request, file_id):
    client_file = get_object_or_404(FileManage, id=file_id)
    client_id = client_file.client.id

    client_file.delete()
    return JsonResponse({'success': True, 'client_id': client_id})

#TODO File Client Download File&Image
@login_required
def file_client_download_file(request, file_id):
    try:
        file_instance = FileManage.objects.get(pk=file_id)
        file_path = file_instance.file_client.path

        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/octet-stream")
            response['Content-Disposition'] = f'attachment; filename="{file_instance.file_client.name}"'
            return response

    except FileManage.DoesNotExist:
        raise Http404("File not found")
    except Exception as e:
        # Log the error for debugging purposes
        print(f"Failed to download file: {e}")
        raise Http404("Failed to download file")

@login_required
def file_client_download_image(request, image_id):
    try:
        image_instance = FileManage.objects.get(pk=image_id)
        image_path = image_instance.image_client.path

        with open(image_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/octet-stream")
            response['Content-Disposition'] = f'attachment; filename="{image_instance.image_client.name}"'
            return response

    except FileManage.DoesNotExist:
        raise Http404("Image not found")
    except Exception as e:
        raise Http404("Failed to download image")

# TODO Engagement
@login_required
def engagement_list(request):
    # ดึงเดือนและปีปัจจุบัน
    current_month = datetime.now().month
    current_year = datetime.now().year

    engagements = Engagement.objects.all().order_by('job_code')
    # engagement_details = EngagementDetail.objects.prefetch_related('engagement', 'engagement_category').all()
    # กรอง engagement_details ตามเดือนปัจจุบัน โดยใช้ start_date และ end_date
    engagement_details = EngagementDetail.objects.filter(
        Q(start_date__year=current_year, start_date__month=current_month) |
        Q(end_date__year=current_year, end_date__month=current_month)
    ).prefetch_related(
        Prefetch('engagement', queryset=Engagement.objects.all()),
        Prefetch('engagement_category', queryset=EngagementCategory.objects.all())
    )

    clients = Client.objects.all()
    total_engagements = engagements.count()
    open_engagements = engagements.filter(status__in=['OPEN_JOB', 'IN_PROGRESS', 'REVIEW', 'PENDING_CLIENT']).count()
    closed_engagements = engagements.filter(status='DONE').count()

    unique_statuses = Engagement.objects.values_list('status', flat=True).distinct()

    return render(request, 'task/engagement/engagement_list.html', {
        'engagements': engagements,
        'engagement_details': engagement_details,
        'clients': clients,
        'total_engagements': total_engagements,
        'open_engagements': open_engagements,
        'closed_engagements': closed_engagements,
        'unique_statuses': unique_statuses,
    })

# TODO Record Engagement
@login_required
def record_engagement(request, engagement_id):
    engagement = get_object_or_404(Engagement, id=engagement_id)
    client_all = Client.objects.values('id','code','company_name')
    return render(request, 'task/engagement/record_engagement.html', {
        'engagement': engagement,
        'client_all':client_all,
    })

# TODO GetDataForEngagement
def get_engagement_type(request):
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        if category_id:
            engagement_types = EngagementType.objects.filter(category_id=category_id).values('id', 'name_th')
            return JsonResponse(list(engagement_types), safe=False)
        else:
            return JsonResponse({'error': 'Category ID is required'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

# TODO Engagement Detail
@login_required
def engagement_detail(request,engagement_id):
    engagement = get_object_or_404(Engagement, id=engagement_id)
    engagement_detail_lists = EngagementDetail.objects.filter(engagement=engagement).all()
    client_list = Client.objects.exclude(status=False).values('id', 'code', 'company_name').order_by('code')
    categories = EngagementCategory.objects.all()
    types = EngagementType.objects.all
    administrators = get_user_model().objects.filter(is_staff=True)
    reviewers = get_user_model().objects.filter(is_superuser=True)
    approvers = get_user_model().objects.filter(is_superuser=True)
    return render(request,'task/engagement/engagement_detail.html', {
        'engagement': engagement,
        'engagement_detail_lists':engagement_detail_lists,
        'client_list':client_list,
        'categories':categories,
        'types':types,
        'administrators':administrators,
        'reviewers':reviewers,
        'approvers':approvers
    })

# TODO Engagement Create
@login_required
def engagement_create(request):
    clients = Client.objects.exclude(status='0').values('id', 'code', 'company_name').order_by('code')
    print(clients)
    reviewers = get_user_model().objects.filter(is_superuser=True)
    approvers = get_user_model().objects.filter(is_superuser=True)
    administrator = get_user_model().objects.filter(is_staff=True)

    user = request.user

    if request.method == 'POST':
        client_id = request.POST.get('client')
        job_code = request.POST.get('job_code')
        service_fee = request.POST.get('service_fee', 0)
        start_date_service = request.POST.get('start_date_service')
        end_date_service = request.POST.get('end_date_service')
        start_date_period = request.POST.get('start_date_period')
        end_date_period = request.POST.get('end_date_period','')
        end_date_period_infinity = request.POST.get('end_date_period_infinity') == 'on'
        admin_id = request.POST.get('admin', '')
        approver_id = request.POST.get('approver', '')
        reviewer_id = request.POST.get('reviewer', '')
        category_id = request.POST.get('category_id')
        type_id = request.POST.get('type_id')

        sdate_service = parse_date(start_date_service)
        edate_service = parse_date(end_date_service)
        sdate_period = parse_date(start_date_period)
        edate_period = parse_date(end_date_period)

        client_instance = get_object_or_404(Client, id=client_id)

        admin_instance = None
        approver_instance = None
        reviewer_instance = None
        
        if admin_id:
            admin_instance = get_object_or_404(get_user_model(), id=admin_id)

        if approver_id:
            approver_instance = get_object_or_404(get_user_model(), id=approver_id)

        if reviewer_id:
            reviewer_instance = get_object_or_404(get_user_model(), id=reviewer_id)

        if Engagement.objects.filter(job_code=job_code).exists():
            messages.error(request, f'รหัสงาน "{job_code}" มีอยู่แล้ว. โปรดใช้รหัสงานอื่น')
        else:
            with transaction.atomic():
                engagement = Engagement.objects.create(
                    client=client_instance,
                    job_code=job_code,
                    service_fee=service_fee,
                    start_date_service=sdate_service,
                    end_date_service=edate_service,
                    start_date_period=sdate_period,
                    end_date_period=edate_period,
                    end_date_period_infinity=end_date_period_infinity,
                    administrator=admin_instance,
                    approver=approver_instance,
                    reviewer=reviewer_instance,
                    status='OPEN_JOB',
                    create_by=user,
                    create_at=timezone.now(),
                    category_id=category_id,
                    type_id=type_id,
                    notes=None,
                )
            return redirect('taskcontrol:record_engagement', engagement_id=engagement.id)

    return render(request, 'task/engagement/engagement_create.html', {
        'clients': clients,
        'user': user,
        'reviewers': reviewers,
        'approvers': approvers,
        'administrator': administrator
    })

# TODO Engagement Update
@login_required
def engagement_update(request, engagement_id):
    engagement = get_object_or_404(Engagement, id=engagement_id)
    clients = Client.objects.exclude(status='0').values('id', 'code', 'company_name').order_by('code')
    reviewers = get_user_model().objects.filter(is_superuser=True)
    approvers = get_user_model().objects.filter(is_superuser=True)
    administrators = get_user_model().objects.filter(is_staff=True)
    user = request.user

    if request.method == 'POST':
        update_service_fee = request.POST.get('update_service_fee')
        update_start_date_service = request.POST.get('update_start_date_service')
        update_end_date_service = request.POST.get('update_end_date_service')
        update_start_date_period = request.POST.get('update_start_date_period')
        update_end_date_period = request.POST.get('update_end_date_period', '')
        update_end_date_period_infinity = request.POST.get('update_end_date_period_infinity') == 'on'
        update_admin_id = request.POST.get('update_admin', '')
        update_approver_id = request.POST.get('update_approver', '')
        update_reviewer_id = request.POST.get('update_reviewer', '')

        sdate_service = parse_date(update_start_date_service)
        edate_service = parse_date(update_end_date_service)
        sdate_period = parse_date(update_start_date_period)
        edate_period = parse_date(update_end_date_period)

        client_id = request.POST.get('client_id')
        client_instance = get_object_or_404(Client, id=client_id)

        admin_instance = None
        approver_instance = None
        reviewer_instance = None

        if update_admin_id:
            admin_instance = get_object_or_404(get_user_model(), id=update_admin_id)

        if update_approver_id:
            approver_instance = get_object_or_404(get_user_model(), id=update_approver_id)

        if update_reviewer_id:
            reviewer_instance = get_object_or_404(get_user_model(), id=update_reviewer_id)

        # Update engagement details
        engagement.client = client_instance
        engagement.service_fee = update_service_fee
        engagement.start_date_service = sdate_service
        engagement.end_date_service = edate_service
        engagement.start_date_period = sdate_period
        engagement.end_date_period = edate_period
        engagement.end_date_period_infinity = update_end_date_period_infinity
        engagement.administrator = admin_instance
        engagement.approver = approver_instance
        engagement.reviewer = reviewer_instance
        engagement.save()

        messages.success(request, 'Engagement has been updated successfully.')
        return redirect('taskcontrol:engagement_detail', engagement_id=engagement.id)

    return render(request, 'task/engagement/engagement_detail.html', {
        'engagement': engagement,
        'clients': clients,
        'user': user,
        'reviewers': reviewers,
        'approvers': approvers,
        'administrators': administrators
    })

# TODO Engagement Deleted
@login_required
def engagement_delete(request, engagement_id):
    engagement = get_object_or_404(Engagement, id=engagement_id)
    engagement.delete()
    messages.success(request, 'ลบรายการนี้เรียบร้อย.')
    return redirect("taskcontrol:engagement_list")

#TODO EngagementJob
@login_required
def engagement_job(request):
    engagement_detail_lists = EngagementDetail.objects.all()
    return render(request,'task/engagement/create_engagement_detail.html', {'engagement_detail_lists': engagement_detail_lists})

#TODO EngagementJob Create 1/2
@login_required
def engagement_job_create(request, engagement_id):
    engagement = get_object_or_404(Engagement, id=engagement_id)
    categories = EngagementCategory.objects.all()
    types = EngagementType.objects.all()
    reviewers = get_user_model().objects.filter(is_superuser=True)
    approvers = get_user_model().objects.filter(is_superuser=True)

    if request.method == 'POST':
        category_id = request.POST.get('engagement_category_id')
        type_id = request.POST.get('engagement_type_id')
        type_name = request.POST.get('type')
        deadline = request.POST.get('deadline')
        notification = request.POST.get('notification')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        review_by = request.POST.get('review_by')
        approved_by = request.POST.get('approved_by')

        review_by = review_by == 'on'
        approved_by = approved_by == 'on'

        # Parse dates
        job_start_date = datetime.strptime(start_date, '%Y-%m-%d')
        job_end_date = datetime.strptime(end_date, '%Y-%m-%d')

        # ตรวจสอบว่าระยะเวลาระหว่างวันเริ่มและวันสิ้นสุดมีเดือนเกินหรือเท่ากับ 1 เดือนหรือไม่
        if (job_end_date - job_start_date).days > 30:
            # คำนวณจำนวนเดือนทั้งหมดที่ต้องสร้าง
            num_months = (job_end_date.year - job_start_date.year) * 12 + job_end_date.month - job_start_date.month + 1
            
            # สร้าง engagement details สำหรับแต่ละเดือน
            current_date = job_start_date
            for _ in range(num_months):
                end_of_month = min(current_date + relativedelta(day=31), job_end_date)
                # กำหนด deadline เป็นวันที่ 15 ของเดือนนั้น ๆ
                deadline_date = min(datetime(current_date.year, current_date.month, 15), end_of_month)
                engagement_detail = create_engagement_detail(
                    engagement, category_id, type_id, type_name, deadline_date, notification,
                    current_date, end_of_month,
                    review_by, approved_by, request.user
                )
                current_date += relativedelta(months=1)
        else:
            # สร้าง engagement detail สำหรับงานในช่วงเวลาที่กำหนด
            engagement_detail = create_engagement_detail(
                engagement, category_id, type_id, type_name, deadline, notification,
                job_start_date, job_end_date,
                review_by, approved_by, request.user
            )

        # Success message
        success_message = 'บันทึกข้อมูลลูกค้าเรียบร้อยแล้ว'
        messages.success(request, success_message)

        return redirect('taskcontrol:engagement_detail', engagement_id=engagement.id)

    engagement_detail_lists = EngagementDetail.objects.filter(engagement=engagement)
    
    return render(request, 'task/engagement/create_engagement_detail.html', {
        'categories': categories,
        'types': types,
        'reviewers': reviewers,
        'approvers': approvers,
        'engagement_detail_lists': engagement_detail_lists,
        'engagement': engagement,
    })

#TODO EngagementJob Create 2/2
def create_engagement_detail(engagement, category_id, type_id, type_name, deadline, notification,
                             start_date, end_date, review_by, approved_by, user):
    # Get or create engagement category and type instances
    engagement_category_instance = get_object_or_404(EngagementCategory, id=category_id)
    engagement_type_instance = get_object_or_404(EngagementType, id=type_id)

    # Create and save engagement detail
    engagement_detail = EngagementDetail.objects.create(
        engagement=engagement,
        engagement_category=engagement_category_instance,
        engagement_type=engagement_type_instance,
        type=type_name,
        deadline=deadline,
        notification=notification,
        start_date=start_date,
        end_date=end_date,
        review_by=review_by,
        approved_by=approved_by,
        create_by=user,
        create_at=timezone.now(),
    )
    return engagement_detail

#TODO EngagementJob Delete
@login_required
def engagement_job_delete(request, engagement_job_id):
    engagement_job = get_object_or_404(EngagementDetail, pk=engagement_job_id)
    engagement_job.delete()
    return JsonResponse({'message': 'Engagement Detail Job deleted successfully'})

#TODO File Engagement
@login_required
def file_engagement_list(request, engagement_id):
    engagement = get_object_or_404(Engagement, id=engagement_id)
    engagement_files = FileManage.objects.filter(engagement=engagement).all()
    return render(request, 'task/engagement/engagement_file.html', {'engagement': engagement, 'engagement_files': engagement_files})

#TODO File Engagement Create
@login_required
def file_engagement_create(request, engagement_id):
    engagement = get_object_or_404(Engagement, id=engagement_id)
    engagement_files = FileManage.objects.filter(engagement=engagement)

    if request.method == 'POST':
        engagement_file = request.FILES.get('engagement_file')
        engagement_description = request.POST.get('engagement_description')
        engagement_image = request.FILES.get('engagement_image')

        user = request.user
        engagement_file = FileManage(
            file_engagement=engagement_file,
            description=engagement_description,
            image_engagement=engagement_image,
            engagement=engagement,
            create_by=user,
        )
        engagement_file.save()
        return redirect('taskcontrol:file_engagement_create', engagement_id=engagement.id)

    return render(request, 'task/engagement/engagement_file.html', {'engagement': engagement, 'engagement_files': engagement_files})

#TODO File Engagement Delete
@login_required
@require_POST
def file_engagement_delete(request, file_id):
    engagement_file = get_object_or_404(FileManage, id=file_id)
    engagement_id = engagement_file.engagement.id

    engagement_file.delete()
    return JsonResponse({'success': True, 'engagement_id': engagement_id})

#TODO File Engagement Download File&Image
@login_required
def download_file_engagement(request, file_id):
    try:
        file_instance = FileManage.objects.get(pk=file_id)
        file_path = file_instance.file_engagement.path

        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/octet-stream")
            response['Content-Disposition'] = f'attachment; filename="{file_instance.file_engagement.name}"'
            return response

    except FileManage.DoesNotExist:
        raise Http404("File not found")
    except Exception as e:
        print(f"Failed to download file: {e}")
        raise Http404("Failed to download file")

@login_required
def download_image_engagement(request, image_id):
    try:
        image_instance = FileManage.objects.get(pk=image_id)
        image_path = image_instance.image_engagement.path

        with open(image_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/octet-stream")
            response['Content-Disposition'] = f'attachment; filename="{image_instance.image_engagement.name}"'
            return response

    except FileManage.DoesNotExist:
        raise Http404("Image not found")
    except Exception as e:
        raise Http404("Failed to download image")

#TODO Dashboard
@login_required
def get_engagement_data(request):
    engagement_data = Engagement.objects.all()
    date_counts = Counter(data.create_at.strftime('%Y-%m-%d') for data in engagement_data)
    
    dates = list(date_counts.keys())
    engagement_counts = list(date_counts.values())
    
    response_data = {
        'dates': dates,
        'engagement_counts': engagement_counts
    }

    return JsonResponse(response_data)

@login_required
def dashboard(request):
    # ดึงข้อมูลจากฐานข้อมูล
    clients = Client.objects.exclude(status='0').all().order_by('code')
    total_clients = clients.count()
    engagements = Engagement.objects.all()
    engagement_details = EngagementDetail.objects.exclude(status='DONE').all().order_by('engagement__job_code')
    total_engagements = engagements.count()
    open_job_engagement = engagements.filter(status__in=STATUS_OPEN_JOB).count()
    done_job_engagement = engagements.filter(status__in=STATUS_DONE).count()
    engagement_categories = EngagementCategory.objects.all()
    engagement_types = EngagementType.objects.filter(category__in=engagement_categories).all()
    administrators = get_user_model().objects.all()

    # tasks = Task.objects.exclude(status='DONE').all()
    # task_count = Task.objects.exclude(status='DONE').count()

    # Get the current month and year
    current_month = timezone.now().month
    current_year = timezone.now().year

    # Filter tasks due in the current month and year
    tasks_due_current_month = Task.objects.exclude(status='DONE').filter(
        Q(due_date__month=current_month, due_date__year=current_year)
    )

    # ส่งข้อมูลไปยัง template
    return render(request, 'task/dashboard.html', {
        'clients': clients,
        'total_clients': total_clients,
        'engagements': engagements,
        'engagement_details': engagement_details,
        'total_engagements': total_engagements,
        'open_job_engagement': open_job_engagement,
        'done_job_engagement': done_job_engagement,
        'engagement_categories': engagement_categories,
        'engagement_types': engagement_types,
        'administrators': administrators,
        'tasks': tasks_due_current_month,
    })

#TODO Dashboard Filter
@login_required
def get_engagement_detail_dashboard(request):
    if request.method == 'GET':
        # Extract parameters from the request
        client_id = request.GET.get('client_id')
        start_date_period = request.GET.get('start_date_period')
        end_date_period = request.GET.get('end_date_period')
        category_id = request.GET.get('category_id')
        deadline_days = request.GET.get('deadline_days')
        per_month = request.GET.get('per_month')
        engagement_type_id = request.GET.get('engagement_type_id')
        near_deadline_3 = request.GET.get('near_deadline_3') == 'true'
        near_deadline_5 = request.GET.get('near_deadline_5') == 'true'
        near_deadline_7 = request.GET.get('near_deadline_7') == 'true'
        near_deadline_14 = request.GET.get('near_deadline_14') == 'true'

        # Query engagement details
        engagement_details = EngagementDetail.objects.all().order_by('engagement__job_code')

        # Apply filters
        if client_id:
            engagement_details = engagement_details.filter(engagement__client_id=client_id)
        if start_date_period:
            engagement_details = engagement_details.filter(engagement__start_date_period__gte=start_date_period)
        if end_date_period:
            engagement_details = engagement_details.filter(engagement__end_date_period__lte=end_date_period)
        if category_id:
            engagement_details = engagement_details.filter(engagement_category_id=category_id)
        if engagement_type_id:
            engagement_details = engagement_details.filter(engagement_type_id=engagement_type_id)
        if deadline_days:
            today = timezone.now().date()
            deadline_date = today + timedelta(days=int(deadline_days))
            engagement_details = engagement_details.filter(deadline__lte=deadline_date)

        # Exclude engagements with status "DONE"
        engagement_details = engagement_details.exclude(status="DONE")
        
        # Filter engagement details based on per_month
        if per_month:
            current_month = timezone.now().month
            current_year = timezone.now().year
            engagement_details = engagement_details.filter(
                engagement__start_date_period__month=current_month, 
                engagement__start_date_period__year=current_year,
                engagement__end_date_period__month=current_month,
                engagement__end_date_period__year=current_year,
            )

        # Filter engagement details based on near deadline options
        if near_deadline_3:
            deadline_3_days = timezone.now().date() + timedelta(days=3)
            engagement_details = engagement_details.filter(deadline__lte=deadline_3_days)

        if near_deadline_5:
            deadline_5_days = timezone.now().date() + timedelta(days=5)
            engagement_details = engagement_details.filter(deadline__lte=deadline_5_days)

        if near_deadline_7:
            deadline_7_days = timezone.now().date() + timedelta(days=7)
            engagement_details = engagement_details.filter(deadline__lte=deadline_7_days)

        if near_deadline_14:
            deadline_14_days = timezone.now().date() + timedelta(days=14)
            engagement_details = engagement_details.filter(deadline__lte=deadline_14_days)

        # Prepare data for engagement details
        engagement_data = []
        for detail in engagement_details:
            remaining_days = (detail.deadline - timezone.now().date()).days if detail.deadline else None
            deadline = detail.deadline.strftime("%d/%m/%Y") if detail.deadline else ''
            engagement_type = detail.engagement_type.name_th if detail.engagement_type else ''
            engagement_data.append({
                'job_code': detail.engagement.job_code,
                'client': detail.engagement.client.company_name if detail.engagement.client else '',
                'type': engagement_type,
                'start_date_period': detail.engagement.start_date_period.strftime("%d/%m/%Y") if detail.engagement.start_date_period else '',
                'end_date_period': detail.engagement.end_date_period.strftime("%d/%m/%Y") if detail.engagement.end_date_period else '',
                'administrator': detail.engagement.administrator.get_full_name() if detail.engagement.administrator else '',
                'deadline': deadline,
                'remaining_days': remaining_days,
                'status': detail.status,
            })

        # Return JSON response
        return JsonResponse({'engagement_details': engagement_data})
    
# def get_engagement_detail_dashboard(request):
#     if request.method == 'GET':
#         # Extract parameters from the request
#         client_id = request.GET.get('client_id')
#         start_date_period = request.GET.get('start_date_period')
#         end_date_period = request.GET.get('end_date_period')
#         category_id = request.GET.get('category_id')
#         deadline_days = request.GET.get('deadline_days')
#         per_month = request.GET.get('per_month')
#         engagement_type_id = request.GET.get('engagement_type_id')

#         # Query engagements
#         engagements = Engagement.objects.all().order_by('job_code')

#         # Apply filters
#         if client_id:
#             engagements = engagements.filter(client_id=client_id)
#         if start_date_period:
#             engagements = engagements.filter(start_date_period__gte=start_date_period)
#         if end_date_period:
#             engagements = engagements.filter(end_date_period__lte=end_date_period)
#         if category_id:
#             engagements = engagements.filter(category_id=category_id)
#         if engagement_type_id:
#             engagements = engagements.filter(type_id=engagement_type_id)
#         if deadline_days:
#             today = timezone.now().date()
#             engagements_with_deadlines = EngagementDetail.objects.filter(
#                 deadline__gt=today,
#                 deadline__lte=F('engagement__end_date_period')
#             ).values('engagement_id')
#             engagements = engagements.filter(id__in=engagements_with_deadlines)

#         # Exclude engagements with status "DONE"
#         engagements = engagements.exclude(status="DONE")
        
#         # Filter engagements based on per_month
#         if per_month:
#             current_month = datetime.now().month
#             current_year = datetime.now().year
#             engagements = engagements.filter(
#                 start_date_period__month=current_month, 
#                 start_date_period__year=current_year,
#                 end_date_period__month=current_month,
#                 end_date_period__year=current_year,
#             )

#         # Prepare data for engagements
#         engagement_data = []
#         for engagement in engagements:
#             engagement_details = EngagementDetail.objects.filter(engagement=engagement)
#             if engagement_details.count() > 1:  # Check if more than one engagement detail exists
#                 for engagement_detail in engagement_details:
#                     remaining_days = (engagement_detail.deadline - datetime.today().date()).days
#                     deadline = engagement_detail.deadline.strftime("%d/%m/%Y") if engagement_detail.deadline else ''
#                     engagement_type = engagement_detail.engagement_type.name_th if engagement_detail.engagement_type else ''
#                     engagement_data.append({
#                         'job_code': engagement.job_code,
#                         'client': engagement.client.company_name if engagement.client else '',
#                         'type': engagement_type,
#                         'start_date_period': engagement.start_date_period.strftime("%d/%m/%Y") if engagement.start_date_period else '',
#                         'end_date_period': engagement.end_date_period.strftime("%d/%m/%Y") if engagement.end_date_period else '',
#                         'administrator': engagement.administrator.get_full_name() if engagement.administrator else '',
#                         'deadline': deadline,
#                         'remaining_days': remaining_days,
#                         'status': engagement.status,
#                     })
#             else:
#                 remaining_days = (engagement_details[0].deadline - datetime.today().date()).days
#                 deadline = engagement_details[0].deadline.strftime("%d/%m/%Y") if engagement_details[0].deadline else ''
#                 engagement_type = engagement_details[0].engagement_type.name_th if engagement_details[0].engagement_type else ''
#                 engagement_data.append({
#                     'job_code': engagement.job_code,
#                     'client': engagement.client.company_name if engagement.client else '',
#                     'type': engagement_type,
#                     'start_date_period': engagement.start_date_period.strftime("%d/%m/%Y") if engagement.start_date_period else '',
#                     'end_date_period': engagement.end_date_period.strftime("%d/%m/%Y") if engagement.end_date_period else '',
#                     'administrator': engagement.administrator.get_full_name() if engagement.administrator else '',
#                     'deadline': deadline,
#                     'remaining_days': remaining_days,
#                     'status': engagement.status,
#                 })


#         # Return JSON response
#         return JsonResponse({'engagements': engagement_data})


#TODO Dashboard Chart
def get_engagement_detail_status(request):
    statuses = ['OPEN_JOB', 'IN_PROGRESS', 'REVIEW', 'PENDING_CLIENT', 'DONE']

    # Filter engagement details by specified statuses and annotate counts
    status_counts = EngagementDetail.objects.filter(status__in=statuses).values('status').annotate(count=Count('status'))

    # Calculate total count
    total_count = sum(item['count'] for item in status_counts)

    # Calculate percentages with handling for zero total_count
    percentages = {item['status']: round((item['count'] / total_count) * 100, 2) if total_count > 0 else 0.00 for item in status_counts}

    # Prepare data to be returned as JSON
    data = {
        'labels': statuses,
        'series': [item['count'] for item in status_counts],
        'percentages': [percentages.get(status, 0) for status in statuses],
    }

    return JsonResponse(data, safe=False)


#TODO Dashboard Accounting
def get_accounting(request):
    statuses = ['OPEN_JOB', 'IN_PROGRESS', 'REVIEW', 'PENDING_CLIENT', 'DONE']
    
    engagement_types = EngagementType.objects.filter(
        category__name_th='บัญชี'
    ).values_list('name_th', flat=True)

    data = {
        'labels': list(engagement_types),
        'series': []
    }

    for status in statuses:
        engagement_details = EngagementDetail.objects.filter(
            engagement_category__name_th='บัญชี',
            status=status
        ).values('engagement_type__name_th')

        series_data = []
        for engagement_type in engagement_types:
            count = engagement_details.filter(engagement_type__name_th=engagement_type).count()
            series_data.append(count)

        data['series'].append({
            'name': status,
            'data': series_data
        })

    return JsonResponse(data, safe=False)

def get_tax(request):
    statuses = ['OPEN_JOB', 'IN_PROGRESS', 'REVIEW', 'PENDING_CLIENT', 'DONE']
    
    engagement_types = EngagementType.objects.filter(
        category__name_th='ภาษี'
    ).values_list('name_th', flat=True)

    data = {
        'labels': list(engagement_types),
        'series': []
    }

    for status in statuses:
        engagement_details = EngagementDetail.objects.filter(
            engagement_category__name_th='ภาษี',
            status=status
        ).values('engagement_type__name_th')

        series_data = []
        for engagement_type in engagement_types:
            count = engagement_details.filter(engagement_type__name_th=engagement_type).count()
            series_data.append(count)

        data['series'].append({
            'name': status,
            'data': series_data
        })

    return JsonResponse(data, safe=False)

def get_payroll(request):
    statuses = ['OPEN_JOB', 'IN_PROGRESS', 'REVIEW', 'PENDING_CLIENT', 'DONE']
    
    engagement_types = EngagementType.objects.filter(
        category__name_th='เงินเดือน'
    ).values_list('name_th', flat=True)

    data = {
        'labels': list(engagement_types),
        'series': []
    }

    for status in statuses:
        engagement_details = EngagementDetail.objects.filter(
            engagement_category__name_th='เงินเดือน',
            status=status
        ).values('engagement_type__name_th')

        series_data = []
        for engagement_type in engagement_types:
            count = engagement_details.filter(engagement_type__name_th=engagement_type).count()
            series_data.append(count)

        data['series'].append({
            'name': status,
            'data': series_data
        })

    return JsonResponse(data, safe=False)

def get_report(request):
    statuses = ['OPEN_JOB', 'IN_PROGRESS', 'REVIEW', 'PENDING_CLIENT', 'DONE']
    
    engagement_types = EngagementType.objects.filter(
        category__name_th='รายงาน'
    ).values_list('name_th', flat=True)

    data = {
        'labels': list(engagement_types),
        'series': []
    }

    for status in statuses:
        engagement_details = EngagementDetail.objects.filter(
            engagement_category__name_th='รายงาน',
            status=status
        ).values('engagement_type__name_th')

        series_data = []
        for engagement_type in engagement_types:
            count = engagement_details.filter(engagement_type__name_th=engagement_type).count()
            series_data.append(count)

        data['series'].append({
            'name': status,
            'data': series_data
        })

    return JsonResponse(data, safe=False)

#TODO Kanban
@login_required
def kanban_board(request):
    today = timezone.now().date()

    current_month = today.month
    current_year = today.year
    previous_month = current_month - 1 if current_month > 1 else 12
    previous_year = current_year if current_month > 1 else current_year - 1

    clients = Client.objects.exclude(status='0').all().order_by('code')
    engagements = Engagement.objects.filter(client__isnull=False)

    # 2 weeks
    fourteen_days_ago = timezone.now() - timezone.timedelta(days=14)

    engagement_details = EngagementDetail.objects.filter(
        (
            Q(start_date__year=current_year, start_date__month=current_month) &
            Q(end_date__year=current_year, end_date__month=current_month)
        ) |
        (
            Q(start_date__year=previous_year, start_date__month=previous_month) &
            Q(end_date__year=current_year, end_date__month=current_month)
        ),
        engagement__in=engagements,
        status__in=['OPEN_JOB', 'IN_PROGRESS', 'REVIEW', 'PENDING_CLIENT', 'DONE']
    ).exclude(
        Q(status='DONE') & Q(completed_at__lte=fourteen_days_ago)
    ).order_by('engagement__job_code')

    engagement_detail = EngagementDetail.objects.all()

    # Update status counts, near deadlines, and date deadlines
    status_counts = get_status_counts(engagement_details)
    update_near_deadline(engagement_details, today)
    date_deadlines = get_date_deadlines(engagement_details, today)

    administrators = get_user_model().objects.all()
    engagement_types = EngagementType.objects.distinct()

    for detail in engagement_details:
        detail.days_remaining = (detail.deadline - today).days

    tasks = Task.objects.filter(status__in=['OPEN_JOB', 'IN_PROGRESS', 'REVIEW', 'PENDING_CLIENT', 'DONE']
    ).exclude(
        Q(status='DONE') & Q(completed_at__lte=fourteen_days_ago)
    ).order_by('number')

    context = {
        'clients': clients,
        'engagements': engagements,
        'engagement_details': engagement_details,
        'engagement_detail': engagement_detail,
        **status_counts,
        'administrators': administrators,
        'engagement_types': engagement_types,
        'today': today,
        'date_deadlines': date_deadlines,
        'tasks': tasks,
    }

    return render(request, 'task/kanban/board.html', context)

#TODO Kanban Update Status
def update_engagement_detail_status(request):
    if request.method == 'POST':
        engagement_detail_id = request.POST.get('engagement_detail_id')
        task_id = request.POST.get('task_id')
        new_status = request.POST.get('new_status')
        
        try:
            # Update engagement detail
            engagement_detail = get_object_or_404(EngagementDetail, pk=engagement_detail_id)
                
            if new_status == 'DONE' and engagement_detail.status != 'DONE':
                engagement_detail.status = 'DONE'
                engagement_detail.completed_at = timezone.now()
            else:
                engagement_detail.status = new_status
                engagement_detail.completed_at = None
            
            engagement_detail.save()

            return JsonResponse({'success': True})
        except EngagementDetail.DoesNotExist:
            return JsonResponse({'error': 'Engagement detail not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

#TODO Kanban Update Status Task
def update_task_status(request):
    if request.method == 'POST':
        task_id = request.POST.get('task_id')
        new_status = request.POST.get('new_status')
        
        try:
            # Update task
            task = get_object_or_404(Task, pk=task_id)
                
            if new_status == 'DONE' and task.status != 'DONE':
                task.status = 'DONE'
                task.completed_at = timezone.now()
            else:
                task.status = new_status
                task.completed_at = None
            task.save()

            return JsonResponse({'success': True})
        except Task.DoesNotExist:
            return JsonResponse({'error': 'Task not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


#TODO Kanban NewTask 
@login_required
def add_new_task(request):
    if request.method == 'POST':
        client_id = request.POST.get('client_id')
        number = request.POST.get('number')
        new_job = request.POST.get('new_job')
        description = request.POST.get('description')
        due_date = request.POST.get('due_date')

        task = Task.objects.create(
            client_id=client_id,
            number=number,
            new_job=new_job,
            description=description,
            due_date=due_date,
            status='OPEN_JOB',
            create_at=timezone.now(),
            update_at=timezone.now()
        )

        task.save()
        return redirect('taskcontrol:kanban_board')

    return render(request, 'task/kanban/new_task.html')

#TODO Kanban Add Comment Engagement Detail
@login_required
def update_engagement_detail_comment(request):
    if request.method == 'POST' and request.is_ajax():
        engagement_detail_id = request.POST.get('engagement_detail_id')
        new_comment = request.POST.get('new_comment')

        engagement_detail = get_object_or_404(EngagementDetail, pk=engagement_detail_id)

        if engagement_detail.comment:
            engagement_detail.comment += "\n" + new_comment
        else:
            engagement_detail.comment = new_comment
        
        engagement_detail.save()

        data = {
            'status': 'success',
            'engagement_detail_id': engagement_detail_id,
            'new_comment': new_comment,
        }

        return JsonResponse(data)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

def get_status_counts(engagement_details):
    return {
        'engagement_details_open': engagement_details.filter(status='OPEN_JOB').count(),
        'engagement_details_inprogress': engagement_details.filter(status='IN_PROGRESS').count(),
        'engagement_details_review': engagement_details.filter(status='REVIEW').count(),
        'engagement_details_pending': engagement_details.filter(status='PENDING_CLIENT').count(),
        'engagement_details_done': engagement_details.filter(status='DONE').count(),
        'engagement_detail_total': engagement_details.count(),
    }

def update_near_deadline(engagement_details, today):
    for detail in engagement_details:
        detail.near_deadline = detail.deadline <= today + timedelta(days=7)

def get_date_deadlines(engagement_details, today):
    return {detail.id: (detail.deadline - today).days for detail in engagement_details}


#TODO Kanban Filter
@login_required
def kanban_board_filter(request):
    engagements = Engagement.objects.filter(client__isnull=False)
    
    current_month = datetime.now().month
    current_year = datetime.now().year
    previous_month = current_month - 1 if current_month > 1 else 12
    previous_year = current_year if current_month > 1 else current_year - 1

    engagement_details = EngagementDetail.objects.filter(
        (
            Q(start_date__year=current_year, start_date__month=current_month) &
            Q(end_date__year=current_year, end_date__month=current_month)
        ) |
        (
            Q(start_date__year=previous_year, start_date__month=previous_month) &
            Q(end_date__year=current_year, end_date__month=current_month)
        ),
        engagement__in=engagements,
        status__in=['OPEN_JOB', 'IN_PROGRESS', 'REVIEW', 'PENDING_CLIENT']
    ).order_by('engagement__job_code')

    today = date.today()

    def get_status_counts(details):
        status_counts = {
            'open_count': details.filter(status="OPEN_JOB").count(),
            'in_progress_count': details.filter(status="IN_PROGRESS").count(),
            'review_count': details.filter(status="REVIEW").count(),
            'pending_client_count': details.filter(status="PENDING_CLIENT").count(),
            'total_count': details.count(),
        }
        return status_counts

    def update_near_deadline(details, current_date):
        for detail in details:
            if (detail.deadline - current_date).days <= 7:
                detail.near_deadline = True
            else:
                detail.near_deadline = False

    status_counts = get_status_counts(engagement_details)
    update_near_deadline(engagement_details, today)

    def get_date_deadlines(details, current_date):
        date_deadlines = {
            'today_count': details.filter(deadline=current_date).count(),
            'future_count': details.filter(deadline__gt=current_date).count(),
            'past_count': details.filter(deadline__lt=current_date).count(),
        }
        return date_deadlines

    date_deadlines = get_date_deadlines(engagement_details, today)

    administrators = get_user_model().objects.all()

    engagement_category = EngagementCategory.objects.all()

    for detail in engagement_details:
        detail.days_remaining = (detail.deadline - today).days

    context = {
        'engagements': engagements,
        'engagement_details': engagement_details,
        **status_counts,
        'administrators': administrators,
        'engagement_category': engagement_category,
        'today': today,
        'date_deadlines': date_deadlines,
        'engagement_detail_total': engagement_details.count(),
    }

    return render(request, 'task/kanban/board_filter.html', context)

def get_engagement_details(request):
    if request.method == 'GET':
        job_code = request.GET.get('job_code')
        engagement = get_object_or_404(Engagement, job_code=job_code)
        engagement_details = EngagementDetail.objects.filter(engagement=engagement)

        modal_content = """
            <div class="row mb-3">
                <div class="col-2">
                    <p class="fw-semibold">วันที่เปิดงาน :</p>
                </div>
                <div class="col-4">
                    {create_at}
                </div>
            </div>
            <div class="row mb-3">
                <div class="col-2">
                    <p class="fw-semibold">ชื่อลูกค้า :</p>
                </div>
                <div class="col-5">
                    {company_name}
                </div>
                <div class="col-2">
                    <span class="fw-semibold">ผู้ดูแล: </span> 
                </div>
                <div class="col-3">
                    {administrator_name}
                </div>
            </div>
            <div class="row mb-3">
                <div class="col-2">
                    <p class="fw-semibold">รอบบัญชี:</p>
                </div>
                <div class="col-5">
                    {start_date_period}
                </div>
                <div class="col-2">
                    <span class="fw-semibold">ผู้ตราจทาน: </span> 
                </div>
                <div class="col-3">
                    {reviewer_name}
                </div>
            </div>
            <div class="row mb-3">
                <div class="col-2">
                    <p class="fw-semibold">หมายเหตุ:</p>
                </div>
                <div class="col-5">
                    {notes}
                </div>
                <div class="col-2">
                    <span class="fw-semibold">ผู้อนุมัติ: </span>
                </div>
                <div class="col-3">
                    {approver_name}
                </div>
            </div>
            <div class="row mb-3">
                <div class="col-2">
                    <p class="fw-semibold">ประเภทงาน :</p>
                </div>
            </div>
        """.format(
            create_at=engagement.create_at.strftime('%d/%m/%Y') if engagement.create_at else "N/A",
            company_name=engagement.client.company_name if engagement.client else "N/A",
            start_date_period=engagement.start_date_period.strftime('%d/%m/%Y') if engagement.start_date_period else "N/A",
            notes=engagement.notes if engagement.notes else "N/A",
            administrator_name=f"{engagement.administrator.first_name} {engagement.administrator.last_name}" if engagement.administrator else "N/A",
            reviewer_name=f"{engagement.reviewer.first_name} {engagement.reviewer.last_name}" if engagement.reviewer else "N/A",
            approver_name=f"{engagement.approver.first_name} {engagement.approver.last_name}" if engagement.approver else "N/A",
        )

        for detail in engagement_details:
            modal_content += """
            <div class="row mb-3">
                <div class="col-2"></div>
                <div class="col-5">
                    {category}
                    <i class="fa-solid fa-angle-right"></i>
                    {type}
                </div>
                <div class="col-2">
                    <span class="fw-semibold">เดดไลน์ :</span>
                </div>
                <div class="col-3">
                    {deadline}
                </div>
            </div>
            """.format(
                category=detail.engagement_category.name_th if detail.engagement_category else "N/A",
                type=detail.engagement_type.name_th if detail.engagement_type else "N/A",
                deadline=detail.deadline.strftime("%d/%m/%Y") if detail.deadline else "N/A"
            )

        return JsonResponse({'modal_content': modal_content})
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)

#TODO Kanban Search
@login_required
def search_filter_engagement_details(request):
    engagements = Engagement.objects.all()
    engagement_details = EngagementDetail.objects.all()
    administrators = get_user_model().objects.all()
    engagement_type = EngagementType.objects.all()
    status_order = ['OPEN_JOB', 'IN_PROCESS', 'PENDING_CLIENT', 'REVIEW', 'DONE']
    engagement_statuses = Engagement.objects.values_list('status', flat=True).distinct().order_by(
        Case(
            *[When(status=s, then=pos) for pos, s in enumerate(status_order)]
        )
    )
    engagement_detail_deadlines = EngagementDetail.objects.filter(engagement__in=engagements).values('id', 'deadline')

    deadlines = [item['deadline'] for item in engagement_detail_deadlines]
    formatted_dates = []
    for date_obj in deadlines:
        formatted_date = date_obj.strftime("%Y-%m-%d")
        formatted_dates.append(formatted_date)

    today = date.today()

    date_deadlines = []
    for formatted_date in formatted_dates:
        deadline_date = datetime.strptime(formatted_date, "%Y-%m-%d").date()
        difference = deadline_date - today
        date_deadlines.append(difference.days)

    status_counts = {}

    return render(request, 'task/kanban/filter_engagements.html', {
        'engagements': engagements,
        'engagement_details': engagement_details,
        'administrators': administrators,
        'engagement_types': engagement_type,
        'date_deadlines': date_deadlines,
        'today' : today,
        'engagement_statuses' : engagement_statuses,
        'status_counts': status_counts,
    })

#TODO Kanban Filter
@login_required
def get_filter_engagement_details(request):
    if request.method == 'GET':
        administrator_id = request.GET.get('administrator_id')
        engagement_type_id = request.GET.get('engagement_type_id')

        engagements = Engagement.objects.all()
        
        if administrator_id:
            engagements = engagements.filter(administrator_id=administrator_id)

        if engagement_type_id:
            engagements = engagements.filter(engagementdetail__engagement_type_id=engagement_type_id)

        if request.GET.get('near_deadline'):
            today = timezone.now().date()
            engagements = engagements.filter(engagementdetail__deadline__gt=today).order_by('engagementdetail__deadline')

        if request.GET.get('per_month'):
            today = timezone.now()
            current_month = today.month
            current_year = today.year

            # หากต้องการให้ช่วงระหว่างเดือนปัจจุบัน (current_month) ถึงเดือนถัดไป (current_month + 1)
            next_month = (current_month % 12) + 1  # หาก current_month เป็น 12 จะได้เป็น 1 (มกราคมของปีถัดไป)
            next_year = current_year if next_month != 1 else current_year + 1  # ถ้า next_month เป็น 1 จะเป็นเดือนของปีถัดไป

            # กรอง engagements เพื่อแสดงข้อมูลที่ start_date_period หรือ end_date_period ตรงกับเดือนปัจจุบันหรืออยู่ระหว่างเดือนปัจจุบัน
            engagements = engagements.filter(
                models.Q(start_date_period__year=current_year, start_date_period__month=current_month) |
                models.Q(end_date_period__year=current_year, end_date_period__month=current_month) |
                (
                    Q(start_date_period__year=current_year, start_date_period__month__lt=current_month) &
                    Q(end_date_period__year=current_year, end_date_period__month__gte=current_month)
                ) |
                (
                    Q(start_date_period__year__lt=current_year) &
                    Q(end_date_period__year=current_year, end_date_period__month__gte=current_month)
                ) |
                (
                    Q(start_date_period__year=current_year, start_date_period__month__lt=current_month) &
                    Q(end_date_period__year__gt=current_year)
                )
            )

        engagement_data = []
        for engagement in engagements:
            engagement_details = engagement.engagementdetail_set.all()
            for engagement_detail in engagement_details:
                deadline = engagement_detail.deadline.strftime("%d/%m/%Y") if engagement_detail.deadline else ''
                engagement_type = engagement_detail.engagement_type.name_th if engagement_detail.engagement_type else ''
                engagement_data.append({
                    'job_code': engagement.job_code,
                    'type': engagement_type,
                    'reviewer': engagement.reviewer.first_name + ' ' + engagement.reviewer.last_name if engagement.reviewer else '',
                    'approver': engagement.approver.first_name + ' ' + engagement.approver.last_name if engagement.approver else '',
                    'administrator': engagement.administrator.first_name + ' ' + engagement.administrator.last_name if engagement.administrator else '',
                    'deadline': deadline,
                    'status': engagement.status,
                })
        return JsonResponse({'engagements': engagement_data})



    
#TODO EngagementCategory
@login_required
def manage_category(request):
    if request.method == 'POST':
        category_name_th = request.POST.get('category_name_th')
        category_name_en = request.POST.get('category_name_en')

        category = EngagementCategory.objects.create(
            name_th=category_name_th,
            name_en=category_name_en,
            create_by=request.user,
            create_at=timezone.now(),
        )
        messages.success(request, "Category created successfully.")
    
    engagement_categories = EngagementCategory.objects.all()
    engagement_types = EngagementType.objects.all()
    return render(request, 'task/setting/engagement_category.html', {'engagement_categories': engagement_categories, 'engagement_types': engagement_types})

#TODO EngagementCategory Update
@login_required
def update_category(request, category_id):
    category = get_object_or_404(EngagementCategory, id=category_id)
    
    if request.method == 'POST':
        new_category_name_th = request.POST.get('new_category_name_th')
        new_category_name_en = request.POST.get('new_category_name_en')

        category.name_th = new_category_name_th
        category.name_en = new_category_name_en
        category.update_by = request.user
        category.update_at = timezone.now()
        category.save()
        messages.success(request, "Category updated successfully.")
    
    return redirect('taskcontrol:manage_category')

#TODO EngagementCategory Deleted
@login_required
def delete_category(request, category_id):
    if request.method == 'POST':
        category = get_object_or_404(EngagementCategory, pk=category_id)
        category.delete()
        messages.success(request, "Category deleted successfully.")
    
    return redirect('taskcontrol:manage_category')

#TODO EngagementType
@login_required
def manage_type(request):
    if request.method == 'POST':
        type_name_th = request.POST.get('type_name_th')
        type_description = request.POST.get('type_description')
        category_id = request.POST.get('category_id')

        category = get_object_or_404(EngagementCategory, id=category_id)
        
        engagement_type = EngagementType.objects.create(
            name_th=type_name_th,
            description=type_description,
            category=category,
            create_by=request.user,
            create_at=timezone.now(),
        )

        messages.success(request, "Type created successfully.")

    engagement_categories = EngagementCategory.objects.all()
    engagement_types = EngagementType.objects.all()
    
    # Render the template with context data
    return render(request, 'task/setting/engagement_type.html', {
        'engagement_categories': engagement_categories,
        'engagement_types': engagement_types
    })

#TODO EngagementType Update
@login_required
def update_type(request, type_id):
    categories = EngagementCategory.objects.all()
    engagement_type = get_object_or_404(EngagementType, id=type_id)

    if request.method == 'POST':
        new_type_name_th = request.POST.get('new_type_name_th')
        new_type_description = request.POST.get('new_type_description')
        category_id = request.POST.get('category_id')

        category = get_object_or_404(EngagementCategory, id=category_id)

        # Update engagement type
        engagement_type.name_th = new_type_name_th
        engagement_type.description = new_type_description
        engagement_type.category = category
        engagement_type.update_by = request.user
        engagement_type.update_at = timezone.now()
        engagement_type.save()

        messages.success(request, "Type updated successfully.")

        return redirect('taskcontrol:manage_type')

    return render(request, 'task/setting/engagement_type.html', {
        'categories': categories,
        'engagement_type': engagement_type,  # Pass the engagement type to the template for rendering if needed
    })

#TODO EngagementType Deleted
@login_required
def delete_type(request, type_id):
    if request.method == 'POST':
        engagement_type = get_object_or_404(EngagementType, pk=type_id)
        engagement_type.delete()
        messages.success(request, "Type deleted successfully.")
        return redirect('taskcontrol:manage_type')

#TODO Channel Create
@login_required
def manage_channel(request):
    if request.method == 'POST':
        channel_name = request.POST.get('channel_name')
        channel_description = request.POST.get('channel_description','')

        channel = Channel.objects.create(
            name=channel_name,
            description=channel_description,
            created_at=timezone.now(),
        )
        channel.save()
    channel_list = Channel.objects.all()
    return render(request, 'task/setting/channel.html', {'channel_list': channel_list})

#TODO Channel Update
@login_required
def update_channel(request, channel_id):
    channel = get_object_or_404(Channel, id=channel_id)
    
    if request.method == 'POST':
        new_channel_name = request.POST.get('new_channel_name')
        new_channel_description = request.POST.get('new_channel_description','')

        channel.name = new_channel_name
        channel.description = new_channel_description
        channel.update_at = timezone.now()
        channel.save()

    return redirect('taskcontrol:manage_channel')

#TODO Channel Deleted
@login_required
def delete_channel(request, channel_id):
    if request.method == 'POST':
        channel = get_object_or_404(Channel, pk=channel_id)
        channel.delete()
        messages.success(request, "Channel deleted successfully.")
    return redirect('taskcontrol:manage_channel')

#TODO RegisterType Create
@login_required
def manage_register_type(request):
    if request.method == 'POST':
        short_name = request.POST.get('short_name')
        name_th = request.POST.get('name_th')
        name_en = request.POST.get('name_en')

        register_type = RegisterType.objects.create(
            short_name=short_name,
            name_th=name_th,
            name_en=name_en,
            create_by=request.user,
            create_at=timezone.now()
        )
        register_type.save()

        return redirect('taskcontrol:manage_register_type')

    register_type_list = RegisterType.objects.all()
    return render(request, 'task/setting/register_type.html', {'register_type_list': register_type_list})

#TODO RegisterType Update
@login_required
def update_register_type(request, register_type_id):
    register_type = get_object_or_404(RegisterType, id=register_type_id)
    
    if request.method == 'POST':
        new_short_name = request.POST.get('short_name')
        new_name_th = request.POST.get('name_th')
        new_name_en = request.POST.get('name_en')

        register_type.short_name = new_short_name
        register_type.name_th = new_name_th
        register_type.name_en = new_name_en
        register_type.update_by = request.user
        register_type.update_at = timezone.now()
        register_type.save()
        return redirect('taskcontrol:manage_register_type') 

    return render(request, 'task/setting/register_type.html', {
        'register_type': register_type,
    })

#TODO RegisterType Deleted
@login_required
def delete_register_type(request, register_type_id):
    if request.method == 'POST':
        register_type = get_object_or_404(RegisterType, pk=register_type_id)
        register_type.delete()
        messages.success(request, "Register type deleted successfully.")
    return redirect('taskcontrol:manage_register_type')
