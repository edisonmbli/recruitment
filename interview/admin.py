from collections import defaultdict
from django.http import HttpResponse
from django.contrib import admin
from interview.models import Candidate
from interview import candidate_field as cf
from django.db.models import Q

import logging
import csv
from datetime import datetime

logger = logging.getLogger(__name__)

# Register your models here.

exportable_fields = ('username', 'city', 'phone', 'bachelor_school', 'master_school', 'degree', 'first_result', 'first_interviewer_user',
                     'second_result', 'second_interviewer_user', 'hr_result', 'hr_score', 'hr_remark', 'hr_interviewer_user')

# define export action


def export_model_as_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    field_list = exportable_fields
    response['Content-Disposition'] = 'attachment; filename=%s-list-%s.csv' % (
        'recruitment-candidates', datetime.now().strftime('%Y-%m-%d-%H-%M-%S'))

    # 写入表头
    writer = csv.writer(response)
    writer.writerow([queryset.model._meta.get_field(
        f).verbose_name.title() for f in field_list])

    for obj in queryset:
        csv_line_values = []
        for field in field_list:
            field_object = queryset.model._meta.get_field(field)
            field_value = field_object.value_from_object(obj)
            csv_line_values.append(field_value)
        writer.writerow(csv_line_values)

    logger.info('%s exported %s candidate records' %
                (request.user, len(queryset)))
    return response


export_model_as_csv.short_description = u'导出为csv文件'
export_model_as_csv.allowed_permissions = ('export',)


# 候选人管理类
class CandidateAdmin(admin.ModelAdmin):
    exclude = ('creator', 'created_date', 'modified_date')

    # ,声明是iterable, 否则会报错
    actions = (export_model_as_csv,)

    # 当前用户是否有导出权限
    def has_export_permission(self, request):
        opts = self.opts
        return request.user.has_perm('%s.%s' % (opts.app_label, 'export'))

    list_display = (
        'username', 'city', 'bachelor_school', 'first_score', 'first_result', 'first_interviewer_user', 'second_result', 'second_interviewer_user', 'hr_score', 'hr_result', 'last_editor')

    # 筛选条件
    list_filter = ('city', 'first_result', 'second_result', 'hr_result',
                   'first_interviewer_user', 'second_interviewer_user', 'hr_interviewer_user')

    # 查询字段
    search_fields = ('username', 'phone', 'email', 'bachelor_school',)

    # 展示排序
    ordering = ('hr_result', 'second_result', 'first_result',)

    # 获取用户组别
    def get_group_names(self, user):
        group_names = []
        for g in user.groups.all():
            group_names.append(g.name)
        return group_names

    # 列表中可以直接编辑的字段, 通过覆盖父类方法来实现
    def get_list_editable(self, request):
        group_names = self.get_group_names(request.user)

        if request.user.is_superuser or 'hr' in group_names:
            return ('first_interviewer_user', 'second_interviewer_user',)
        return ()

    def get_changelist_instance(self, request):
        """
        override admin method and list_editable property value
        with values returned by our custom method implementation.
        """
        self.list_editable = self.get_list_editable(request)
        return super(CandidateAdmin, self).get_changelist_instance(request)

    # 详情页readonly字段制定
    def get_readonly_fields(self, request, obj):
        group_names = self.get_group_names(request.user)

        if '面试官' in group_names:
            logger.info("interviewer is in user's group for %s" %
                        request.user.username)
            return ('first_interviewer_user', 'second_interviewer_user',)
        return ()

    # 数据字段的权限控制：一面面试官仅填写一面反馈， 二面面试官可以填写二面反馈
    def get_fieldsets(self, request, obj=None):
        group_names = self.get_group_names(request.user)

        if 'interviewer' in group_names and obj.first_interviewer_user == request.user:
            return cf.default_fieldsets_first

        if 'interviewer' in group_names and obj.second_interviewer_user == request.user:
            return cf.default_fieldsets_second

        return cf.default_fieldsets

    # 对于非管理员，非HR，获取自己是一面面试官或者二面面试官的候选人集合:s
    def get_queryset(self, request):
        qs = super(CandidateAdmin, self).get_queryset(request)

        group_names = self.get_group_names(request.user)
        if request.user.is_superuser or 'hr' in group_names:
            return qs
        return Candidate.objects.filter(Q(first_interview_user=request.user) | Q(second_interviewer_user=request.user))


admin.site.register(Candidate, CandidateAdmin)
