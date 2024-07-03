from taskcontrol.models import *
from django.db.models import F ,Q
from datetime import datetime, timedelta
from django.shortcuts import render,redirect

def notification(request):
    # Filter EngagementDetail
    # #notification condition
    # ## status not equal 'Done'
    # ## Reviewer of approver
    # ## owner and near deadline or before deadline folow by notifation day

    # Check auth
    if request.user.is_authenticated:

        # Filter EngagementDetail
        engagement_result =   EngagementDetail.objects.exclude(
                             Q(status='DONE')
                        ).filter(
                            Q(create_by=request.user) &
                            (
                                Q(deadline__lte=datetime.today()) |
                                Q(deadline__range=(datetime.now() - timedelta(days=1)*(F('notification')),datetime.now()))
                            ) 
                            |
                                (
                                    Q(engagement__reviewer= request.user) |
                                    Q(engagement__approver= request.user)  
                                )
                        )
        # Filter Task
        task_result =   Task.objects.exclude(
                            Q(status='DONE')
                        ).filter(
                            Q(create_by=request.user) &
                            Q(due_date__lte=datetime.today())
                        )
        
        # Filter Result
        # noti_result = engagement_result.union(task_result)
        return {
            'count': engagement_result.count(),
            'notification_detail': engagement_result,
        }
    else :
        return {
            'count': 0,
            'notification_detail': [],
        }
    
