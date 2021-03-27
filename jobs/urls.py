from django.conf.urls import url
from django.urls import path
from jobs import views

urlpatterns = [
    # 职位列表
    url(r"^joblist/", views.joblist, name="joblist"),

    # 职位详情
    url(r"^job/(?P<job_id>\d+)/$", views.detail, name="detail"),

    # 提交简历
    path('resume/add/', views.ResumeCreateView.as_view(), name="resume-add"),

    # 简历详情页
    path('resume/<int:pk>/', views.ResumeDetailView.as_view(), name='resume-detail'),

    path("", views.joblist, name="name")
]
