from taskcontrol.models import *
from django.db.models import F ,Q
from datetime import datetime, timedelta

def notification(request):

    review_noti = EngagementDetail.objects.exclude(
                        status='DONE'
                ).filter(
                    Q(engagement__reviewer= request.user) |
                    Q(engagement__approver= request.user)  
                )
    other_result = EngagementDetail.objects.filter(
                        Q(deadline__lte=datetime.now()) |
                        Q(deadline__range=[datetime.now() - timedelta(days=1)*F('notification') , datetime.now() ]) &
                        Q(create_by=request.user)
                    )
    result_noti = review_noti | other_result
    user_id = request.user.id
    return {
        'count': result_noti.count(),
        'notification_detail': result_noti,
        'get_user': user_id
    }