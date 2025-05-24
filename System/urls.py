from django.urls import path
from django.shortcuts import redirect
from . import views
from .views import (
    add_student, dashboard, login_view, logout_view,
    edit_student,
    current_school_year,
    get_evaluation_tables,
    view_evaluation_table,
    save_evaluation,
    load_evaluation_data,

    get_student_performance_data,
    upload_pdf,
    delete_pdf,
    pdf_view,
    manage_account,
    manage_student_session,
    forgot_password,
    create_announcement,
    view_announcements,
    delete_announcement,
    student_full_report,
    evaluation_management,
    get_saved_evaluation_forms,
    get_evaluation_form_data,
    update_evaluation_form,
    parent_evaluation_tables,
    teacher_evaluation_tables,
    get_all_students,
    readonly_evaluation_forms,
    get_evaluation_data,
)

urlpatterns = [
    path('', login_view, name='login'),
    path('login/', login_view, name='login_page'),
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('dashboard/', dashboard, name='dashboard'),
    path('add_student/', add_student, name='add_student'),
    path('logout/', logout_view, name='logout'),
    path('pdf_view/', pdf_view, name='pdf_view'),
    path('student-full-report/', student_full_report, name='student_full_report'),
    path('get-student-performance-data/', get_student_performance_data, name='get_student_performance_data'),
    path('upload-pdf/', upload_pdf, name='upload_pdf'),
    path('delete-pdf/<int:pdf_id>/', delete_pdf, name='delete_pdf'),
    path('manage-account/', manage_account, name='manage_account'),
    path('manage-student-session/', manage_student_session, name='manage_student_session'),
    path('account_settings/', views.account_settings, name='account_settings'),
    
    # Announcement URLs
    path('create-announcement/', create_announcement, name='create_announcement'),
    path('announcements/', view_announcements, name='view_announcements'),
    path('delete-announcement/<int:announcement_id>/', delete_announcement, name='delete_announcement'),
    path('get-recent-announcements/', views.get_recent_announcements, name='get_recent_announcements'),   
    # Calendar URLs
    path('events/', views.get_events, name='get_events'),
    path('events/add/', views.add_event, name='add_event'),
    path('events/delete/<int:event_id>/', views.delete_event, name='delete_event'),
    # Student Edit URLs

    path('get-all-students/', get_all_students, name='get_all_students'),
    path('edit-student/', edit_student, name='edit_student'),
    # Evaluation Management URL
    path('evaluation-management/', evaluation_management, name='evaluation_management'),
    path('save-evaluation-management/', views.save_evaluation_management, name='save_evaluation_management'),  
    # Saved Evaluation Forms URLs
    path('get-saved-evaluation-forms/', get_saved_evaluation_forms, name='get_saved_evaluation_forms'),
    path('get-evaluation-form-data/<int:form_id>/', get_evaluation_form_data, name='get_evaluation_form_data'),
    path('update-evaluation-form/<int:form_id>/', update_evaluation_form, name='update_evaluation_form'),
    path('get-evaluation-tables/', get_evaluation_tables, name='get_evaluation_tables'),
    path('view-evaluation-table/<int:table_id>/', view_evaluation_table, name='view_evaluation_table'),
    path('parent-evaluation-tables/', parent_evaluation_tables, name='parent_evaluation_tables'),
    path('teacher-evaluation-tables/', teacher_evaluation_tables, name='teacher_evaluation_tables'),
    path('save-evaluation/<int:table_id>/', save_evaluation, name='save_evaluation'),
    path('load-evaluation-data/<int:table_id>/', load_evaluation_data, name='load_evaluation_data'),
    path('readonly-evaluation-forms/', views.readonly_evaluation_forms, name='readonly_evaluation_forms'),
    path('get-evaluation-data/', get_evaluation_data, name='get_evaluation_data'),
    path('evaluation-gross/', lambda request: redirect('student_full_report'), name='evaluation_gross'),
    path('teacher-evaluations/', views.view_teacher_evaluations, name='teacher_evaluations'),
    path('current-school-year/', current_school_year, name='current_school_year'),
    path('generate-next-school-year/<int:school_year_id>/', views.generate_next_school_year, name='generate_next_school_year'),
]
