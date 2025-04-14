from django.urls import path
from . import views
from .views import (
    add_student, dashboard, login_view, logout_view, evaluation_checklist,
    submit_cognitive_evaluation, submit_expressive_evaluation,
    submit_fine_evaluation, submit_gross_evaluation,
    submit_receptive_evaluation,
    submit_selfhelp_evaluation,

    
    performance_view,
    settings_view,

    
    evaluation_gross,
    evaluation_self,
    evaluation_expressive,
    evaluation_cognitive,
    evaluation_social,

    
    ParentEvaluationSelf,
    ParentEvaluationGross,
    ParentEvaluationSocial,
    ParentEvaluationExpressive,
    ParentEvaluationCognitive,
    student_profile,
    messages_view,
    get_student_performance_data,
)

urlpatterns = [
    path('', login_view, name='login'),
    path('login/', login_view, name='login_page'),
    path('dashboard/', dashboard, name='dashboard'),
    path('add_student/', add_student, name='add_student'),
    path('logout/', logout_view, name='logout'),
    path('evaluation-checklist/', evaluation_checklist, name='evaluation_checklist'),
    path('submit-cognitive-evaluation/', submit_cognitive_evaluation, name='submit_cognitive_evaluation'),
    path('submit-expressive-evaluation/', submit_expressive_evaluation, name='submit_expressive_evaluation'),
    path('submit-fine-evaluation/', submit_fine_evaluation, name='submit_fine_evaluation'),
    path('submit-gross-evaluation/', submit_gross_evaluation, name='submit_gross_evaluation'),
    path('submit-receptive-evaluation/', submit_receptive_evaluation, name='submit_receptive_evaluation'),
    path('submit-selfhelp-evaluation/', submit_selfhelp_evaluation, name='submit_selfhelp_evaluation'),
    path('performance/', performance_view, name='performance'),
    path('settings/', settings_view, name='settings'),
    path('messages/', messages_view, name='messages_view'),
    path('evaluation-gross/', evaluation_gross, name='evaluation_gross'),
    path('evaluation-self/', evaluation_self, name='evaluation_self'),
    path('evaluation-expressive/', evaluation_expressive, name='evaluation_expressive'),
    path('evaluation-cognitive/', evaluation_cognitive, name='evaluation_cognitive'),
    path('evaluation-social/', evaluation_social, name='evaluation_social'),
    path('parent-evaluation-self/', ParentEvaluationSelf, name='parent_evaluation_self'),
    path('parent-evaluation-self/<int:student_id>/', ParentEvaluationSelf, name='parent_evaluation_self_with_id'),
    path('parent-evaluation-gross/', ParentEvaluationGross, name='parent_evaluation_gross'),
    path('parent-evaluation-gross/<int:student_id>/', ParentEvaluationGross, name='parent_evaluation_gross_with_id'),
    path('parent-evaluation-social/', ParentEvaluationSocial, name='parent_evaluation_social'),
    path('parent-evaluation-social/<int:student_id>/', ParentEvaluationSocial, name='parent_evaluation_social_with_id'),
    path('parent-evaluation-expressive/', ParentEvaluationExpressive, name='parent_evaluation_expressive'),
    path('parent-evaluation-expressive/<int:student_id>/', ParentEvaluationExpressive, name='parent_evaluation_expressive_with_id'),
    path('parent-evaluation-cognitive/', ParentEvaluationCognitive, name='parent_evaluation_cognitive'),
    path('parent-evaluation-cognitive/<int:student_id>/', ParentEvaluationCognitive, name='parent_evaluation_cognitive_with_id'),
    path('comparison/', views.comparison_view, name='comparison_view'),
    path('student-performance/', views.student_performance, name='student_performance'),
    path('student-profile/', student_profile, name='student_profile'),
    path('api/student-performance-data/', get_student_performance_data, name='get_student_performance_data'),
]
