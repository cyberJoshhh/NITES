from django.shortcuts import render, redirect, get_object_or_404
from .models import (
    Student, EvaluationRecord, CognitiveEvaluation, ExpressiveEvaluation, 
    FineEvaluation, GrossEvaluation, ReceptiveEvaluation, SelfHelpEvaluation, 
    ParentSelfHelpEvaluation, ParentGrossEvaluation, ParentSocialEvaluation, 
    ParentExpressiveEvaluation, ParentCognitiveEvaluation, Announcement, 
    EvaluationPDF, PDFFile, GrossMotorPDF, SelfHelpPDF, SocialPDF, ExpressivePDF,
    CognitivePDF
)
from .forms import StudentForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_protect, csrf_exempt
import json
from django.db.models import Q
from django.utils import timezone
from datetime import date
import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from django.core.files.base import ContentFile
from datetime import datetime
from django.urls import reverse




@login_required
def dashboard(request):
    # Get the logged-in user's username
    username = request.user.username
    
    # Check if the user corresponds to a student account
    student = None
    scores = None
    
    # Try to find student by username
    student = Student.objects.filter(username=username).first()
    
    if student:
        # This is a student account
        # Get recent announcements for notifications
        recent_announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')[:3]
        
        context = {
            'student': student,
            'gross_evaluations': GrossEvaluation.objects.all(),
            'fine_evaluations': FineEvaluation.objects.all(),
            'self_help_evaluations': SelfHelpEvaluation.objects.all(),
            'expressive_evaluations': ExpressiveEvaluation.objects.all(),
            'receptive_evaluations': ReceptiveEvaluation.objects.all(),
            'cognitive_evaluations': CognitiveEvaluation.objects.all(),
            'recent_announcements': recent_announcements
        }
        context['debug'] = True
        return render(request, "PDash.html", context)
    else:
        # This is a teacher/admin
        students = Student.objects.all()
        # Get the total number of users
        users_count = User.objects.count()
        # Count evaluations (you can adjust this based on your needs)
        evaluations_count = (GrossEvaluation.objects.count() + 
                            FineEvaluation.objects.count() + 
                            SelfHelpEvaluation.objects.count() + 
                            ExpressiveEvaluation.objects.count() + 
                            ReceptiveEvaluation.objects.count() + 
                            CognitiveEvaluation.objects.count())
        
        # Get recent announcements for teacher dashboard
        recent_announcements = Announcement.objects.all().order_by('-created_at')[:5]
        
        return render(request, "TDash.html", {
            "students": students,
            "users_count": users_count,
            "evaluations_count": evaluations_count,
            "messages_count": 0,  # You can replace this with actual message count if you have a message model
            "recent_announcements": recent_announcements
        })


def add_student(request):
    if request.method == 'POST':
        try:
            # Get username and password from the form
            username = request.POST.get('username')
            password = request.POST.get('password')
            
            # Create a User account in Django's auth system
            user = User.objects.create_user(
                username=username,
                password=password  # create_user handles password hashing
            )
            user.save()
            
            # Create student record with the correct field names
            student = Student(
                child_name=request.POST.get('child_name'),
                sex=request.POST.get('sex'),
                dob=request.POST.get('dob'),
                handedness=request.POST.get('handedness'),
                studying=request.POST.get('studying'),
                birth_order=request.POST.get('birth_order'),
                num_siblings=int(request.POST.get('num_siblings')),
                
                # Address information
                address=request.POST.get('address'),
                barangay=request.POST.get('barangay'),
                municipality=request.POST.get('municipality'),
                province=request.POST.get('province'),
                region=request.POST.get('region'),
                
                # Father's information
                father_name=request.POST.get('father_name'),
                father_age=int(request.POST.get('father_age')),
                father_occupation=request.POST.get('father_occupation'),
                father_education=request.POST.get('father_education'),
                
                # Mother's information
                mother_name=request.POST.get('mother_name'),
                mother_age=int(request.POST.get('mother_age')),
                mother_occupation=request.POST.get('mother_occupation'),
                mother_education=request.POST.get('mother_education'),
                
                # Login credentials - link to the User account
                username=username,
                password=password  # Consider removing this field as it's now in auth_user
            )
            student.save()
        except Exception as e:
            messages.error(request, f'Error registering student: {str(e)}')
            return render(request, 'add_student.html')
    
    return render(request, 'add_student.html')
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Try to authenticate using Django's auth system (for teachers/admin)
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')  # This will go to TDash for admin, PDash for students
        else:
            # Check if this is a student account directly in the Student table
            student = Student.objects.filter(username=username, password=password).first()
            
            if student:
                # Create or update Django user for this student account
                try:
                    # Get the user if it exists
                    user = User.objects.get(username=username)
                    # Update password to match Student model for consistent authentication
                    user.set_password(password)
                    user.save()
                except User.DoesNotExist:
                    # Create a new user if doesn't exist
                    user = User.objects.create_user(
                        username=username,
                        password=password
                    )
                
                # Login the user through Django's auth system
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    return redirect('dashboard')  # Redirect to dashboard
            
            # If all attempts fail, show error
            messages.error(request, 'Invalid username or password')
            return render(request, 'Login.html', {'error': 'Invalid username or password'})
    
    # Display messages from redirects (like from password reset)
    return render(request, 'Login.html')
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def evaluation_checklist(request):
    domain = request.GET.get('domain', 'gross_motor')  # Default to gross motor if no domain specified
    template_name = f"evaluation_checklists/{domain}.html"
    return render(request, template_name)

@csrf_protect
def cognitive_checklist(request, student_id):
    student = Student.objects.get(id=student_id)
    context = {
        'student': student
    }
    return render(request, 'evaluation_checklists/cognitive.html', context)

def get_checklist_context(student_id):
    try:
        student = Student.objects.get(id=student_id)
        latest_eval = EvaluationRecord.objects.filter(student=student).order_by('-evaluation_number').first()
        evaluation_number = (latest_eval.evaluation_number + 1 if latest_eval else 1) if latest_eval and latest_eval.evaluation_number < 3 else 3
        
        return {
            'student': student,
            'evaluation_number': evaluation_number
        }
    except Student.DoesNotExist:
        return None

def checklist_view(request, student_id, domain):
    context = get_checklist_context(student_id)
    if context is None:
        return redirect('dashboard')
    
    # Add domain-specific context
    domain_titles = {
        'cognitive': 'Cognitive Domain',
        'fine_motor': 'Fine Motor Domain',
        'gross_motor': 'Gross Motor Domain',
        'self_help': 'Self-Help Domain',
        'expressive_language': 'Expressive Language Domain',
        'receptive_language': 'Receptive Language Domain'
    }
    
    context.update({
        'current_domain': domain,
        'domain_title': domain_titles[domain]
    })
    
    return render(request, f'evaluation_checklists/{domain}.html', context)

def submit_cognitive_evaluation(request):
    if request.method == 'POST':
        student_name = request.POST.get('student_name')
        eval1_score = int(request.POST.get('eval1_score', 0) or 0)
        eval2_score = int(request.POST.get('eval2_score', 0) or 0)
        eval3_score = int(request.POST.get('eval3_score', 0) or 0)

        CognitiveEvaluation.objects.create(
            student_name=student_name,
            eval1_score=eval1_score,
            eval2_score=eval2_score,
            eval3_score=eval3_score
        )

        messages.success(request, 'Evaluation submitted successfully!')
        return redirect('dashboard')  # or wherever you want to redirect after submission

    return redirect('dashboard')


def submit_expressive_evaluation(request):
    if request.method == 'POST':
        student_name = request.POST.get('student_name')
        eval1_score = int(request.POST.get('eval1_score', 0) or 0)
        eval2_score = int(request.POST.get('eval2_score', 0) or 0)
        eval3_score = int(request.POST.get('eval3_score', 0) or 0)

        ExpressiveEvaluation.objects.create(
            student_name=student_name,
            eval1_score=eval1_score,
            eval2_score=eval2_score,
            eval3_score=eval3_score
        )

        messages.success(request, 'Evaluation submitted successfully!')
        return redirect('dashboard')

def submit_fine_evaluation(request):
    if request.method == 'POST':
        student_name = request.POST.get('student_name')
        # Convert scores to integers, default to 0 if empty
        eval1_score = int(request.POST.get('eval1_score', 0) or 0)
        eval2_score = int(request.POST.get('eval2_score', 0) or 0)
        eval3_score = int(request.POST.get('eval3_score', 0) or 0)

        FineEvaluation.objects.create(
            student_name=student_name,
            eval1_score=eval1_score,
            eval2_score=eval2_score,
            eval3_score=eval3_score
        )

        messages.success(request, 'Evaluation submitted successfully!')
        return redirect('dashboard')

    return redirect('dashboard')

def submit_gross_evaluation(request):
    if request.method == 'POST':
        student_name = request.POST.get('student_name')
        eval1_score = int(request.POST.get('eval1_score', 0) or 0)
        eval2_score = int(request.POST.get('eval2_score', 0) or 0)
        eval3_score = int(request.POST.get('eval3_score', 0) or 0)

        GrossEvaluation.objects.create(
            student_name=student_name,
            eval1_score=eval1_score,
            eval2_score=eval2_score,
            eval3_score=eval3_score
        )

        messages.success(request, 'Evaluation submitted successfully!')
        return redirect('dashboard')  # or wherever you want to redirect after submission

    return redirect('dashboard')

def submit_receptive_evaluation(request):
    if request.method == 'POST':
        student_name = request.POST.get('student_name')
        eval1_score = int(request.POST.get('eval1_score', 0) or 0)
        eval2_score = int(request.POST.get('eval2_score', 0) or 0)
        eval3_score = int(request.POST.get('eval3_score', 0) or 0)

        ReceptiveEvaluation.objects.create(
            student_name=student_name,
            eval1_score=eval1_score,
            eval2_score=eval2_score,
            eval3_score=eval3_score
        )

        messages.success(request, 'Evaluation submitted successfully!')
        return redirect('dashboard')  # or wherever you want to redirect after submission

    return redirect('dashboard')

def submit_selfhelp_evaluation(request):
    if request.method == 'POST':
        student_name = request.POST.get('student_name')
        eval1_score = int(request.POST.get('eval1_score', 0) or 0)
        eval2_score = int(request.POST.get('eval2_score', 0) or 0)
        eval3_score = int(request.POST.get('eval3_score', 0) or 0)

        SelfHelpEvaluation.objects.create(
            student_name=student_name,
            eval1_score=eval1_score,
            eval2_score=eval2_score,
            eval3_score=eval3_score
        )
        messages.success(request, 'Evaluation submitted successfully!')
        return redirect('dashboard')  # or wherever you want to redirect after submission

    return redirect('dashboard')

@login_required
def performance_view(request):
    # Get all students
    students = Student.objects.all()
    
    # Get all evaluation data
    gross_evaluations = GrossEvaluation.objects.all()
    fine_evaluations = FineEvaluation.objects.all()
    self_help_evaluations = SelfHelpEvaluation.objects.all()
    receptive_evaluations = ReceptiveEvaluation.objects.all()
    expressive_evaluations = ExpressiveEvaluation.objects.all()
    cognitive_evaluations = CognitiveEvaluation.objects.all()
    
    # Add users_count for consistency with other views
    users_count = User.objects.count()
    evaluations_count = (GrossEvaluation.objects.count() + 
                        FineEvaluation.objects.count() + 
                        SelfHelpEvaluation.objects.count() + 
                        ExpressiveEvaluation.objects.count() + 
                        ReceptiveEvaluation.objects.count() + 
                        CognitiveEvaluation.objects.count())
    
    context = {
        'students': students,
        'gross_evaluations': gross_evaluations,
        'fine_evaluations': fine_evaluations,
        'self_help_evaluations': self_help_evaluations,
        'receptive_evaluations': receptive_evaluations,
        'expressive_evaluations': expressive_evaluations,
        'cognitive_evaluations': cognitive_evaluations,
        'users_count': users_count,
        'evaluations_count': evaluations_count,
        'messages_count': 0
    }
    return render(request, "performance.html", context)


def pdf_view(request):
    """
    View function for the settings page.
    """
    from .models import PDFFile
    pdf_files = PDFFile.objects.all().order_by('-uploaded_at')
    return render(request, 'PDFFiles.html', {'pdf_files': pdf_files})

def evaluation_gross(request):
    # Get username
    username = request.user.username
    
    # Find student by username
    student = Student.objects.filter(username=username).first()
    
    context = {
        'student': student,
        'active_domain': 'gross'
    }
    
    return render(request, 'pevalgross.html', context)


def evaluation_self(request):
    # Get username
    username = request.user.username
    
    # Find student by username
    student = Student.objects.filter(username=username).first()
    
    context = {
        'student': student,
        'active_domain': 'self'
    }
    
    return render(request, 'pevalself.html', context)

def evaluation_expressive(request):
    # Get username
    username = request.user.username
    
    # Find student by username
    student = Student.objects.filter(username=username).first()
    
    context = {
        'student': student,
        'active_domain': 'expressive'
    }
    
    return render(request, 'pevalexpressive.html', context)

def evaluation_cognitive(request):
    # Get username
    username = request.user.username
    
    # Find student by username
    student = Student.objects.filter(username=username).first()
    
    context = {
        'student': student,
        'active_domain': 'cognitive'
    }
    
    return render(request, 'pevalcognitive.html', context)

def evaluation_social(request):
    # Get username
    username = request.user.username
    
    # Find student by username
    student = Student.objects.filter(username=username).first()
    
    context = {
        'student': student,
        'active_domain': 'social'
    }
    
    return render(request, 'pevalsocial.html', context)

@login_required
def ParentEvaluationSelf(request, student_id=None):
    """
    Display and handle the parent self-help evaluation form.
    If method is GET, displays the form.
    If method is POST, processes the submission.
    """
    # GET request - display the evaluation form
    if request.method == 'GET':
        student = None
        if student_id:
            student = get_object_or_404(Student, id=student_id)
        
        context = {
            'student': student,
        }
        
        return render(request, 'pevalself.html', context)
    
    # POST request - process the evaluation data
    elif request.method == 'POST':
        try:
            # Extract form data
            student_name = request.POST.get('student_name', '')
            
            # If we have student_id but not student_name, try to get the name
            if student_id and not student_name:
                try:
                    student = Student.objects.get(id=student_id)
                    student_name = student.child_name
                except Student.DoesNotExist:
                    return JsonResponse({
                        'status': 'error', 
                        'message': 'Student not found'
                    }, status=404)
            
            # Get evaluation scores
            eval1_score = int(request.POST.get('eval1_score', 0))
            eval2_score = int(request.POST.get('eval2_score', 0))
            eval3_score = int(request.POST.get('eval3_score', 0))
            
            # Get comments if any
            comments_json = request.POST.get('comments', '[]')
            
            # Create a new evaluation record
            evaluation = ParentSelfHelpEvaluation(
                student_name=student_name,
                eval1_score=eval1_score,
                eval2_score=eval2_score,
                eval3_score=eval3_score
            )
            evaluation.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Self-Help evaluation saved successfully',
                'evaluation_id': evaluation.id
            })
            
        except ValueError as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Invalid data format: {str(e)}'
            }, status=400)
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error saving evaluation: {str(e)}'
            }, status=500)
    
    # Other request methods
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method. GET or POST required.'
    }, status=405)

@login_required
def ParentEvaluationGross(request, student_id=None):
    """
    Display and handle the parent gross motor evaluation form.
    If method is GET, displays the form.
    If method is POST, processes the submission.
    """
    # GET request - display the evaluation form
    if request.method == 'GET':
        student = None
        if student_id:
            student = get_object_or_404(Student, id=student_id)
        
        context = {
            'student': student,
        }
        
        return render(request, 'pevalgross.html', context)
    
    # POST request - process the evaluation data
    elif request.method == 'POST':
        try:
            # Extract form data
            student_name = request.POST.get('student_name', '')
            
            # If we have student_id but not student_name, try to get the name
            if student_id and not student_name:
                try:
                    student = Student.objects.get(id=student_id)
                    student_name = student.child_name
                except Student.DoesNotExist:
                    return JsonResponse({
                        'status': 'error', 
                        'message': 'Student not found'
                    }, status=404)
            
            # Get evaluation scores
            eval1_score = int(request.POST.get('eval1_score', 0))
            eval2_score = int(request.POST.get('eval2_score', 0))
            eval3_score = int(request.POST.get('eval3_score', 0))
            
            # Get comments if any
            comments_json = request.POST.get('comments', '[]')
            
            # Create a new evaluation record
            evaluation = ParentGrossEvaluation(
                student_name=student_name,
                eval1_score=eval1_score,
                eval2_score=eval2_score,
                eval3_score=eval3_score
            )
            evaluation.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Gross Motor evaluation saved successfully',
                'evaluation_id': evaluation.id
            })
            
        except ValueError as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Invalid data format: {str(e)}'
            }, status=400)
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error saving evaluation: {str(e)}'
            }, status=500)
    
    # Other request methods
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method. GET or POST required.'
    }, status=405)

@login_required
def ParentEvaluationSocial(request, student_id=None):
    """
    Display and handle the parent social-emotional evaluation form.
    If method is GET, displays the form.
    If method is POST, processes the submission.
    """
    # GET request - display the evaluation form
    if request.method == 'GET':
        student = None
        if student_id:
            student = get_object_or_404(Student, id=student_id)
        
        context = {
            'student': student,
        }
        
        return render(request, 'pevalsocial.html', context)
    
    # POST request - process the evaluation data
    elif request.method == 'POST':
        try:
            # Extract form data
            student_name = request.POST.get('student_name', '')
            
            # If we have student_id but not student_name, try to get the name
            if student_id and not student_name:
                try:
                    student = Student.objects.get(id=student_id)
                    student_name = student.child_name
                except Student.DoesNotExist:
                    return JsonResponse({
                        'status': 'error', 
                        'message': 'Student not found'
                    }, status=404)
            
            # Get evaluation scores
            eval1_score = int(request.POST.get('eval1_score', 0))
            eval2_score = int(request.POST.get('eval2_score', 0))
            eval3_score = int(request.POST.get('eval3_score', 0))
            
            # Get comments if any
            comments_json = request.POST.get('comments', '[]')
            
            # Create a new evaluation record
            evaluation = ParentSocialEvaluation(
                student_name=student_name,
                eval1_score=eval1_score,
                eval2_score=eval2_score,
                eval3_score=eval3_score
            )
            evaluation.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Social-Emotional evaluation saved successfully',
                'evaluation_id': evaluation.id
            })
            
        except ValueError as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Invalid data format: {str(e)}'
            }, status=400)
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error saving evaluation: {str(e)}'
            }, status=500)
    
    # Other request methods
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method. GET or POST required.'
    }, status=405)

@login_required
def ParentEvaluationExpressive(request, student_id=None):
    """
    Display and handle the parent expressive language evaluation form.
    If method is GET, displays the form.
    If method is POST, processes the submission.
    """
    # GET request - display the evaluation form
    if request.method == 'GET':
        student = None
        if student_id:
            student = get_object_or_404(Student, id=student_id)
        
        context = {
            'student': student,
        }
        
        return render(request, 'pevalexpressive.html', context)
    
    # POST request - process the evaluation data
    elif request.method == 'POST':
        try:
            # Extract form data
            student_name = request.POST.get('student_name', '')
            
            # If we have student_id but not student_name, try to get the name
            if student_id and not student_name:
                try:
                    student = Student.objects.get(id=student_id)
                    student_name = student.child_name
                except Student.DoesNotExist:
                    return JsonResponse({
                        'status': 'error', 
                        'message': 'Student not found'
                    }, status=404)
            
            # Get evaluation scores
            eval1_score = int(request.POST.get('eval1_score', 0))
            eval2_score = int(request.POST.get('eval2_score', 0))
            eval3_score = int(request.POST.get('eval3_score', 0))
            
            # Get comments if any
            comments_json = request.POST.get('comments', '[]')
            
            # Create a new evaluation record
            evaluation = ParentExpressiveEvaluation(
                student_name=student_name,
                eval1_score=eval1_score,
                eval2_score=eval2_score,
                eval3_score=eval3_score
            )
            evaluation.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Expressive Language evaluation saved successfully',
                'evaluation_id': evaluation.id
            })
            
        except ValueError as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Invalid data format: {str(e)}'
            }, status=400)
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error saving evaluation: {str(e)}'
            }, status=500)
    
    # Other request methods
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method. GET or POST required.'
    }, status=405)

@login_required
def ParentEvaluationCognitive(request, student_id=None):
    """
    Display and handle the parent cognitive evaluation form.
    If method is GET, displays the form.
    If method is POST, processes the submission.
    """
    # GET request - display the evaluation form
    if request.method == 'GET':
        student = None
        if student_id:
            student = get_object_or_404(Student, id=student_id)
        
        context = {
            'student': student,
        }
        
        return render(request, 'pevalcognitive.html', context)
    
    # POST request - process the evaluation data
    elif request.method == 'POST':
        try:
            # Extract form data
            student_name = request.POST.get('student_name', '')
            
            # If we have student_id but not student_name, try to get the name
            if student_id and not student_name:
                try:
                    student = Student.objects.get(id=student_id)
                    student_name = student.child_name
                except Student.DoesNotExist:
                    return JsonResponse({
                        'status': 'error', 
                        'message': 'Student not found'
                    }, status=404)
            
            # Get evaluation scores
            eval1_score = int(request.POST.get('eval1_score', 0))
            eval2_score = int(request.POST.get('eval2_score', 0))
            eval3_score = int(request.POST.get('eval3_score', 0))
            
            # Get comments if any
            comments_json = request.POST.get('comments', '[]')
            
            # Create a new evaluation record
            evaluation = ParentCognitiveEvaluation(
                student_name=student_name,
                eval1_score=eval1_score,
                eval2_score=eval2_score,
                eval3_score=eval3_score
            )
            evaluation.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Cognitive evaluation saved successfully',
                'evaluation_id': evaluation.id
            })
            
        except ValueError as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Invalid data format: {str(e)}'
            }, status=400)
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error saving evaluation: {str(e)}'
            }, status=500)
    
    # Other request methods
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method. GET or POST required.'
    }, status=405)

def comparison_view(request):
    search_query = request.GET.get('search', '')
    student_name = request.GET.get('student_name', '')
    
    # Get list of students for the search dropdown
    students = set()
    
    # Collect student names from various evaluation tables
    if search_query:
        # Search across multiple evaluation tables with case-insensitive search
        gross_students = GrossEvaluation.objects.filter(student_name__icontains=search_query).values_list('student_name', flat=True)
        fine_students = FineEvaluation.objects.filter(student_name__icontains=search_query).values_list('student_name', flat=True)
        self_help_students = SelfHelpEvaluation.objects.filter(student_name__icontains=search_query).values_list('student_name', flat=True)
        cognitive_students = CognitiveEvaluation.objects.filter(student_name__icontains=search_query).values_list('student_name', flat=True)
        
        # Add to set to remove duplicates
        students.update(gross_students)
        students.update(fine_students)
        students.update(self_help_students)
        students.update(cognitive_students)
        
        # Sort the students alphabetically
        students = sorted(students)
    
    # Only fetch evaluation data if a specific student is selected
    if student_name:
        # Fetch teacher evaluations
        teacher_gross = GrossEvaluation.objects.filter(student_name=student_name).first()
        teacher_fine = FineEvaluation.objects.filter(student_name=student_name).first()
        teacher_self_help = SelfHelpEvaluation.objects.filter(student_name=student_name).first()
        teacher_receptive = ReceptiveEvaluation.objects.filter(student_name=student_name).first()
        teacher_expressive = ExpressiveEvaluation.objects.filter(student_name=student_name).first()
        teacher_cognitive = CognitiveEvaluation.objects.filter(student_name=student_name).first()
        
        # Fetch parent evaluations
        parent_gross = ParentGrossEvaluation.objects.filter(student_name=student_name).first()
        parent_self_help = ParentSelfHelpEvaluation.objects.filter(student_name=student_name).first()
        parent_social = ParentSocialEvaluation.objects.filter(student_name=student_name).first()
        parent_expressive = ParentExpressiveEvaluation.objects.filter(student_name=student_name).first()
        parent_cognitive = ParentCognitiveEvaluation.objects.filter(student_name=student_name).first()
        
        # Create data for JSON
        teacher_data = {
            'gross_motor': [
                teacher_gross.eval1_score if teacher_gross else 0,
                teacher_gross.eval2_score if teacher_gross else 0,
                teacher_gross.eval3_score if teacher_gross else 0
            ],
            'fine_motor': [
                teacher_fine.eval1_score if teacher_fine else 0,
                teacher_fine.eval2_score if teacher_fine else 0,
                teacher_fine.eval3_score if teacher_fine else 0
            ],
            'self_help': [
                teacher_self_help.eval1_score if teacher_self_help else 0,
                teacher_self_help.eval2_score if teacher_self_help else 0,
                teacher_self_help.eval3_score if teacher_self_help else 0
            ],
            'receptive': [
                teacher_receptive.eval1_score if teacher_receptive else 0,
                teacher_receptive.eval2_score if teacher_receptive else 0,
                teacher_receptive.eval3_score if teacher_receptive else 0
            ],
            'expressive': [
                teacher_expressive.eval1_score if teacher_expressive else 0,
                teacher_expressive.eval2_score if teacher_expressive else 0,
                teacher_expressive.eval3_score if teacher_expressive else 0
            ],
            'cognitive': [
                teacher_cognitive.eval1_score if teacher_cognitive else 0,
                teacher_cognitive.eval2_score if teacher_cognitive else 0,
                teacher_cognitive.eval3_score if teacher_cognitive else 0
            ]
        }
        
        parent_data = {
            'gross_motor': [
                parent_gross.eval1_score if parent_gross else 0,
                parent_gross.eval2_score if parent_gross else 0,
                parent_gross.eval3_score if parent_gross else 0
            ],
            'self_help': [
                parent_self_help.eval1_score if parent_self_help else 0,
                parent_self_help.eval2_score if parent_self_help else 0,
                parent_self_help.eval3_score if parent_self_help else 0
            ],
            'social': [
                parent_social.eval1_score if parent_social else 0,
                parent_social.eval2_score if parent_social else 0,
                parent_social.eval3_score if parent_social else 0
            ],
            'expressive': [
                parent_expressive.eval1_score if parent_expressive else 0,
                parent_expressive.eval2_score if parent_expressive else 0,
                parent_expressive.eval3_score if parent_expressive else 0
            ],
            'cognitive': [
                parent_cognitive.eval1_score if parent_cognitive else 0,
                parent_cognitive.eval2_score if parent_cognitive else 0,
                parent_cognitive.eval3_score if parent_cognitive else 0
            ]
        }
        
        context = {
            'student_name': student_name,
            'teacher_data_json': json.dumps(teacher_data),
            'parent_data_json': json.dumps(parent_data),
            'teacher_evaluations': {
                'gross': teacher_gross,
                'fine': teacher_fine,
                'self_help': teacher_self_help,
                'receptive': teacher_receptive,
                'expressive': teacher_expressive,
                'cognitive': teacher_cognitive
            },
            'parent_evaluations': {
                'gross': parent_gross,
                'self_help': parent_self_help,
                'social': parent_social,
                'expressive': parent_expressive,
                'cognitive': parent_cognitive
            },
            'has_data': True
        }
    else:
        context = {
            'has_data': False
        }
    
    # Always include these in the context
    context['search_query'] = search_query
    context['students'] = students
    
    return render(request, 'comparison.html', context)

def student_performance(request):
    """
    View function that displays the overall performance of a student based on student name.
    Accessible directly via URL with a query parameter or through a search form.
    """
    # Get student name from request parameters
    student_name = request.GET.get('student_name', '')
    
    if not student_name:
        # Check if the logged-in user is a student
        username = request.user.username
        
        # Try to find student by username
        student = Student.objects.filter(username=username).first()
        
        if student:
            # This is a student, get their name
            student_name = student.child_name
        else:
            # If no student name provided and not a student, render a search form
            return render(request, 'student_search.html', {
                'has_data': False,
                'show_search': True
            })
    
    try:
        # Check if the student exists
        student = Student.objects.filter(child_name__iexact=student_name).first()
        
        if not student:
            # Try a more flexible search
            student = Student.objects.filter(child_name__icontains=student_name).first()
        
        if not student:
            # No student found with that name
            return render(request, 'student_performance.html', {
                'has_data': False,
                'error_message': "No student found with that name. Please check spelling and try again."
            })
        
        # Use the exact student name from database for subsequent queries
        student_name = student.child_name
        print(f"Found student: {student_name}")
        
        # Get all evaluation data for this student
        # Use case-insensitive exact match on the student name from the database
        teacher_gross = GrossEvaluation.objects.filter(student_name__iexact=student_name).first()
        teacher_fine = FineEvaluation.objects.filter(student_name__iexact=student_name).first()
        teacher_self_help = SelfHelpEvaluation.objects.filter(student_name__iexact=student_name).first()
        teacher_receptive = ReceptiveEvaluation.objects.filter(student_name__iexact=student_name).first()
        teacher_expressive = ExpressiveEvaluation.objects.filter(student_name__iexact=student_name).first()
        teacher_cognitive = CognitiveEvaluation.objects.filter(student_name__iexact=student_name).first()
        
        # Get parent evaluations data
        parent_gross = ParentGrossEvaluation.objects.filter(student_name__iexact=student_name).first()
        parent_self_help = ParentSelfHelpEvaluation.objects.filter(student_name__iexact=student_name).first()
        parent_social = ParentSocialEvaluation.objects.filter(student_name__iexact=student_name).first()
        parent_expressive = ParentExpressiveEvaluation.objects.filter(student_name__iexact=student_name).first()
        parent_cognitive = ParentCognitiveEvaluation.objects.filter(student_name__iexact=student_name).first()
        
        # Create data for JSON visualization
        teacher_data = {
            'gross_motor': [
                teacher_gross.eval1_score if teacher_gross else 0,
                teacher_gross.eval2_score if teacher_gross else 0,
                teacher_gross.eval3_score if teacher_gross else 0
            ],
            'fine_motor': [
                teacher_fine.eval1_score if teacher_fine else 0,
                teacher_fine.eval2_score if teacher_fine else 0,
                teacher_fine.eval3_score if teacher_fine else 0
            ],
            'self_help': [
                teacher_self_help.eval1_score if teacher_self_help else 0,
                teacher_self_help.eval2_score if teacher_self_help else 0,
                teacher_self_help.eval3_score if teacher_self_help else 0
            ],
            'receptive': [
                teacher_receptive.eval1_score if teacher_receptive else 0,
                teacher_receptive.eval2_score if teacher_receptive else 0,
                teacher_receptive.eval3_score if teacher_receptive else 0
            ],
            'expressive': [
                teacher_expressive.eval1_score if teacher_expressive else 0,
                teacher_expressive.eval2_score if teacher_expressive else 0,
                teacher_expressive.eval3_score if teacher_expressive else 0
            ],
            'cognitive': [
                teacher_cognitive.eval1_score if teacher_cognitive else 0,
                teacher_cognitive.eval2_score if teacher_cognitive else 0,
                teacher_cognitive.eval3_score if teacher_cognitive else 0
            ]
        }
        
        parent_data = {
            'gross_motor': [
                parent_gross.eval1_score if parent_gross else 0,
                parent_gross.eval2_score if parent_gross else 0,
                parent_gross.eval3_score if parent_gross else 0
            ],
            'self_help': [
                parent_self_help.eval1_score if parent_self_help else 0,
                parent_self_help.eval2_score if parent_self_help else 0,
                parent_self_help.eval3_score if parent_self_help else 0
            ],
            'social': [
                parent_social.eval1_score if parent_social else 0,
                parent_social.eval2_score if parent_social else 0,
                parent_social.eval3_score if parent_social else 0
            ],
            'expressive': [
                parent_expressive.eval1_score if parent_expressive else 0,
                parent_expressive.eval2_score if parent_expressive else 0,
                parent_expressive.eval3_score if parent_expressive else 0
            ],
            'cognitive': [
                parent_cognitive.eval1_score if parent_cognitive else 0,
                parent_cognitive.eval2_score if parent_cognitive else 0,
                parent_cognitive.eval3_score if parent_cognitive else 0
            ]
        }
        
        # Calculate total scores for each evaluation period
        teacher_eval1_total = (
            (teacher_gross.eval1_score if teacher_gross else 0) +
            (teacher_fine.eval1_score if teacher_fine else 0) +
            (teacher_self_help.eval1_score if teacher_self_help else 0) +
            (teacher_receptive.eval1_score if teacher_receptive else 0) +
            (teacher_expressive.eval1_score if teacher_expressive else 0) +
            (teacher_cognitive.eval1_score if teacher_cognitive else 0)
        )
        
        teacher_eval2_total = (
            (teacher_gross.eval2_score if teacher_gross else 0) +
            (teacher_fine.eval2_score if teacher_fine else 0) +
            (teacher_self_help.eval2_score if teacher_self_help else 0) +
            (teacher_receptive.eval2_score if teacher_receptive else 0) +
            (teacher_expressive.eval2_score if teacher_expressive else 0) +
            (teacher_cognitive.eval2_score if teacher_cognitive else 0)
        )
        
        teacher_eval3_total = (
            (teacher_gross.eval3_score if teacher_gross else 0) +
            (teacher_fine.eval3_score if teacher_fine else 0) +
            (teacher_self_help.eval3_score if teacher_self_help else 0) +
            (teacher_receptive.eval3_score if teacher_receptive else 0) +
            (teacher_expressive.eval3_score if teacher_expressive else 0) +
            (teacher_cognitive.eval3_score if teacher_cognitive else 0)
        )
        
        parent_eval1_total = (
            (parent_gross.eval1_score if parent_gross else 0) +
            (parent_self_help.eval1_score if parent_self_help else 0) +
            (parent_social.eval1_score if parent_social else 0) +
            (parent_expressive.eval1_score if parent_expressive else 0) +
            (parent_cognitive.eval1_score if parent_cognitive else 0)
        )
        
        parent_eval2_total = (
            (parent_gross.eval2_score if parent_gross else 0) +
            (parent_self_help.eval2_score if parent_self_help else 0) +
            (parent_social.eval2_score if parent_social else 0) +
            (parent_expressive.eval2_score if parent_expressive else 0) +
            (parent_cognitive.eval2_score if parent_cognitive else 0)
        )
        
        parent_eval3_total = (
            (parent_gross.eval3_score if parent_gross else 0) +
            (parent_self_help.eval3_score if parent_self_help else 0) +
            (parent_social.eval3_score if parent_social else 0) +
            (parent_expressive.eval3_score if parent_expressive else 0) +
            (parent_cognitive.eval3_score if parent_cognitive else 0)
        )
        
        # Calculate progress for display
        progress_data = {
            'teacher_progress': calculate_progress(teacher_eval1_total, teacher_eval3_total),
            'parent_progress': calculate_progress(parent_eval1_total, parent_eval3_total)
        }
        
        # Get evaluation collections for charts
        gross_evaluations = GrossEvaluation.objects.filter(student_name__iexact=student_name)
        fine_evaluations = FineEvaluation.objects.filter(student_name__iexact=student_name)
        self_help_evaluations = SelfHelpEvaluation.objects.filter(student_name__iexact=student_name)
        receptive_evaluations = ReceptiveEvaluation.objects.filter(student_name__iexact=student_name)
        expressive_evaluations = ExpressiveEvaluation.objects.filter(student_name__iexact=student_name)
        cognitive_evaluations = CognitiveEvaluation.objects.filter(student_name__iexact=student_name)
        social_evaluations = ParentSocialEvaluation.objects.filter(student_name__iexact=student_name)
        
        # If no data found, create sample data for UI testing
        if (teacher_eval1_total == 0 and teacher_eval2_total == 0 and teacher_eval3_total == 0 and
            parent_eval1_total == 0 and parent_eval2_total == 0 and parent_eval3_total == 0):
            
            print(f"No evaluation data found for student: {student_name}")
            # Create sample data for demonstration purposes
            teacher_eval1_total = 25
            teacher_eval2_total = 35
            teacher_eval3_total = 50
            parent_eval1_total = 20
            parent_eval2_total = 30
            parent_eval3_total = 45
            
            # Recalculate progress with sample data
            progress_data = {
                'teacher_progress': calculate_progress(teacher_eval1_total, teacher_eval3_total),
                'parent_progress': calculate_progress(parent_eval1_total, parent_eval3_total)
            }
        
        return render(request, 'student_performance.html', {
            'student': student,
            'student_name': student_name,
            'teacher_data_json': json.dumps(teacher_data),
            'parent_data_json': json.dumps(parent_data),
            'progress_data': progress_data,
            'teacher_evaluations': {
                'gross': teacher_gross,
                'fine': teacher_fine,
                'self_help': teacher_self_help,
                'receptive': teacher_receptive,
                'expressive': teacher_expressive,
                'cognitive': teacher_cognitive
            },
            'parent_evaluations': {
                'gross': parent_gross,
                'self_help': parent_self_help,
                'social': parent_social,
                'expressive': parent_expressive,
                'cognitive': parent_cognitive
            },
            'teacher_eval1_total': teacher_eval1_total,
            'teacher_eval2_total': teacher_eval2_total,
            'teacher_eval3_total': teacher_eval3_total,
            'parent_eval1_total': parent_eval1_total,
            'parent_eval2_total': parent_eval2_total,
            'parent_eval3_total': parent_eval3_total,
            'gross_evaluations': gross_evaluations,
            'fine_evaluations': fine_evaluations,
            'self_help_evaluations': self_help_evaluations,
            'receptive_evaluations': receptive_evaluations,
            'expressive_evaluations': expressive_evaluations,
            'cognitive_evaluations': cognitive_evaluations,
            'social_evaluations': social_evaluations,
            'has_data': True
        })
        
    except Exception as e:
        import traceback
        print(f"Error in student_performance view: {str(e)}")
        print(traceback.format_exc())
        return render(request, 'student_performance.html', {
            'has_data': False,
            'error_message': f"An error occurred: {str(e)}"
        })

def calculate_progress(initial_score, final_score):
    """Helper function to calculate progress percentage between two scores"""
    if initial_score == 0:
        return 0  # Avoid division by zero
    
    progress = ((final_score - initial_score) / initial_score) * 100
    return max(0, progress)  # Don't show negative progress

@login_required
def student_profile(request):
    """
    View function to display a student's profile information.
    """
    # Get the logged-in user's username
    username = request.user.username
    
    # Try to find student by username
    student = Student.objects.filter(username=username).first()
    
    if not student:
        messages.error(request, "No student profile found for this account.")
        return redirect('dashboard')
    
    # Calculate age from date of birth
    today = date.today()
    age = today.year - student.dob.year - ((today.month, today.day) < (student.dob.month, student.dob.day))
    
    context = {
        'student': student,
        'age': age,
        'active_section': 'profile'
    }
    
    return render(request, 'student_profile.html', context)

@login_required
def manage_account(request):
    """
    View function to allow users to manage their account settings.
    Users can change their username and password.
    """
    user = request.user
    success_message = None
    error_message = None
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'change_username':
            new_username = request.POST.get('new_username')
            
            # Check if username already exists
            if User.objects.filter(username=new_username).exists():
                error_message = "Username already exists. Please choose another one."
            else:
                # If the user is a student, update both User and Student models
                student = Student.objects.filter(username=user.username).first()
                if student:
                    student.username = new_username
                    student.save()
                
                # Update auth user
                user.username = new_username
                user.save()
                success_message = "Username updated successfully!"
                
        elif action == 'change_password':
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            # Verify current password
            if not user.check_password(current_password):
                error_message = "Current password is incorrect."
            elif new_password != confirm_password:
                error_message = "New passwords do not match."
            elif len(new_password) < 8:
                error_message = "Password must be at least 8 characters long."
            else:
                # Set new password
                user.set_password(new_password)
                user.save()
                
                # If user is a student, update Student model too
                student = Student.objects.filter(username=user.username).first()
                if student:
                    student.password = new_password
                    student.save()
                
                success_message = "Password updated successfully! Please log in again."
                logout(request)
                return redirect('login')
    
    context = {
        'user': user,
        'success_message': success_message,
        'error_message': error_message,
    }
    
    return render(request, 'manage_account.html', context)

@login_required
def get_student_performance_data(request):
    """
    API view function that returns a student's performance data in JSON format.
    Used for populating the performance modal.
    """
    # Get student name from request parameters
    student_name = request.GET.get('student_name', '')
    
    if not student_name:
        return JsonResponse({
            'status': 'error',
            'message': 'Student name is required'
        }, status=400)
    
    try:
        # Check if the student exists
        student = Student.objects.filter(child_name__iexact=student_name).first()
        
        if not student:
            return JsonResponse({
                'status': 'error',
                'message': 'Student not found'
            }, status=404)
        
        # Get all evaluation data for this student
        teacher_gross = GrossEvaluation.objects.filter(student_name__iexact=student_name).first()
        teacher_fine = FineEvaluation.objects.filter(student_name__iexact=student_name).first()
        teacher_self_help = SelfHelpEvaluation.objects.filter(student_name__iexact=student_name).first()
        teacher_receptive = ReceptiveEvaluation.objects.filter(student_name__iexact=student_name).first()
        teacher_expressive = ExpressiveEvaluation.objects.filter(student_name__iexact=student_name).first()
        teacher_cognitive = CognitiveEvaluation.objects.filter(student_name__iexact=student_name).first()
        
        # Get parent evaluations data
        parent_gross = ParentGrossEvaluation.objects.filter(student_name__iexact=student_name).first()
        parent_self_help = ParentSelfHelpEvaluation.objects.filter(student_name__iexact=student_name).first()
        parent_social = ParentSocialEvaluation.objects.filter(student_name__iexact=student_name).first()
        parent_expressive = ParentExpressiveEvaluation.objects.filter(student_name__iexact=student_name).first()
        parent_cognitive = ParentCognitiveEvaluation.objects.filter(student_name__iexact=student_name).first()
        
        # Create data for table display
        table_data = {
            'gross_motor': {
                'teacher_eval1': teacher_gross.eval1_score if teacher_gross else 0,
                'teacher_eval2': teacher_gross.eval2_score if teacher_gross else 0,
                'teacher_eval3': teacher_gross.eval3_score if teacher_gross else 0,
                'parent_eval1': parent_gross.eval1_score if parent_gross else 0,
                'parent_eval2': parent_gross.eval2_score if parent_gross else 0,
                'parent_eval3': parent_gross.eval3_score if parent_gross else 0,
            },
            'fine_motor': {
                'teacher_eval1': teacher_fine.eval1_score if teacher_fine else 0,
                'teacher_eval2': teacher_fine.eval2_score if teacher_fine else 0,
                'teacher_eval3': teacher_fine.eval3_score if teacher_fine else 0,
                'parent_eval1': 'N/A',
                'parent_eval2': 'N/A',
                'parent_eval3': 'N/A',
            },
            'self_help': {
                'teacher_eval1': teacher_self_help.eval1_score if teacher_self_help else 0,
                'teacher_eval2': teacher_self_help.eval2_score if teacher_self_help else 0,
                'teacher_eval3': teacher_self_help.eval3_score if teacher_self_help else 0,
                'parent_eval1': parent_self_help.eval1_score if parent_self_help else 0,
                'parent_eval2': parent_self_help.eval2_score if parent_self_help else 0,
                'parent_eval3': parent_self_help.eval3_score if parent_self_help else 0,
            },
            'receptive': {
                'teacher_eval1': teacher_receptive.eval1_score if teacher_receptive else 0,
                'teacher_eval2': teacher_receptive.eval2_score if teacher_receptive else 0,
                'teacher_eval3': teacher_receptive.eval3_score if teacher_receptive else 0,
                'parent_eval1': 'N/A',
                'parent_eval2': 'N/A',
                'parent_eval3': 'N/A',
            },
            'expressive': {
                'teacher_eval1': teacher_expressive.eval1_score if teacher_expressive else 0,
                'teacher_eval2': teacher_expressive.eval2_score if teacher_expressive else 0,
                'teacher_eval3': teacher_expressive.eval3_score if teacher_expressive else 0,
                'parent_eval1': parent_expressive.eval1_score if parent_expressive else 0,
                'parent_eval2': parent_expressive.eval2_score if parent_expressive else 0,
                'parent_eval3': parent_expressive.eval3_score if parent_expressive else 0,
            },
            'cognitive': {
                'teacher_eval1': teacher_cognitive.eval1_score if teacher_cognitive else 0,
                'teacher_eval2': teacher_cognitive.eval2_score if teacher_cognitive else 0,
                'teacher_eval3': teacher_cognitive.eval3_score if teacher_cognitive else 0,
                'parent_eval1': parent_cognitive.eval1_score if parent_cognitive else 0,
                'parent_eval2': parent_cognitive.eval2_score if parent_cognitive else 0,
                'parent_eval3': parent_cognitive.eval3_score if parent_cognitive else 0,
            },
            'social': {
                'teacher_eval1': 'N/A',
                'teacher_eval2': 'N/A',
                'teacher_eval3': 'N/A',
                'parent_eval1': parent_social.eval1_score if parent_social else 0,
                'parent_eval2': parent_social.eval2_score if parent_social else 0,
                'parent_eval3': parent_social.eval3_score if parent_social else 0,
            }
        }
        
        # Create data for charts
        chart_data = {
            'labels': ['1st Evaluation', '2nd Evaluation', '3rd Evaluation'],
            'datasets': [
                {
                    'label': 'Gross Motor',
                    'data': [
                        teacher_gross.eval1_score if teacher_gross else 0,
                        teacher_gross.eval2_score if teacher_gross else 0,
                        teacher_gross.eval3_score if teacher_gross else 0
                    ],
                    'borderColor': 'rgb(255, 99, 132)',
                    'backgroundColor': 'rgba(255, 99, 132, 0.2)'
                },
                {
                    'label': 'Fine Motor',
                    'data': [
                        teacher_fine.eval1_score if teacher_fine else 0,
                        teacher_fine.eval2_score if teacher_fine else 0,
                        teacher_fine.eval3_score if teacher_fine else 0
                    ],
                    'borderColor': 'rgb(54, 162, 235)',
                    'backgroundColor': 'rgba(54, 162, 235, 0.2)'
                },
                {
                    'label': 'Self Help',
                    'data': [
                        teacher_self_help.eval1_score if teacher_self_help else 0,
                        teacher_self_help.eval2_score if teacher_self_help else 0,
                        teacher_self_help.eval3_score if teacher_self_help else 0
                    ],
                    'borderColor': 'rgb(75, 192, 192)',
                    'backgroundColor': 'rgba(75, 192, 192, 0.2)'
                },
                {
                    'label': 'Receptive Language',
                    'data': [
                        teacher_receptive.eval1_score if teacher_receptive else 0,
                        teacher_receptive.eval2_score if teacher_receptive else 0,
                        teacher_receptive.eval3_score if teacher_receptive else 0
                    ],
                    'borderColor': 'rgb(153, 102, 255)',
                    'backgroundColor': 'rgba(153, 102, 255, 0.2)'
                },
                {
                    'label': 'Expressive Language',
                    'data': [
                        teacher_expressive.eval1_score if teacher_expressive else 0,
                        teacher_expressive.eval2_score if teacher_expressive else 0,
                        teacher_expressive.eval3_score if teacher_expressive else 0
                    ],
                    'borderColor': 'rgb(255, 159, 64)',
                    'backgroundColor': 'rgba(255, 159, 64, 0.2)'
                },
                {
                    'label': 'Cognitive',
                    'data': [
                        teacher_cognitive.eval1_score if teacher_cognitive else 0,
                        teacher_cognitive.eval2_score if teacher_cognitive else 0,
                        teacher_cognitive.eval3_score if teacher_cognitive else 0
                    ],
                    'borderColor': 'rgb(255, 205, 86)',
                    'backgroundColor': 'rgba(255, 205, 86, 0.2)'
                }
            ]
        }
        
        # Calculate totals
        totals = {
            'gross_motor': sum([
                table_data['gross_motor']['teacher_eval1'] if isinstance(table_data['gross_motor']['teacher_eval1'], int) else 0,
                table_data['gross_motor']['teacher_eval2'] if isinstance(table_data['gross_motor']['teacher_eval2'], int) else 0,
                table_data['gross_motor']['teacher_eval3'] if isinstance(table_data['gross_motor']['teacher_eval3'], int) else 0,
                table_data['gross_motor']['parent_eval1'] if isinstance(table_data['gross_motor']['parent_eval1'], int) else 0,
                table_data['gross_motor']['parent_eval2'] if isinstance(table_data['gross_motor']['parent_eval2'], int) else 0,
                table_data['gross_motor']['parent_eval3'] if isinstance(table_data['gross_motor']['parent_eval3'], int) else 0
            ]),
            'fine_motor': sum([
                table_data['fine_motor']['teacher_eval1'] if isinstance(table_data['fine_motor']['teacher_eval1'], int) else 0,
                table_data['fine_motor']['teacher_eval2'] if isinstance(table_data['fine_motor']['teacher_eval2'], int) else 0,
                table_data['fine_motor']['teacher_eval3'] if isinstance(table_data['fine_motor']['teacher_eval3'], int) else 0
            ]),
            'self_help': sum([
                table_data['self_help']['teacher_eval1'] if isinstance(table_data['self_help']['teacher_eval1'], int) else 0,
                table_data['self_help']['teacher_eval2'] if isinstance(table_data['self_help']['teacher_eval2'], int) else 0,
                table_data['self_help']['teacher_eval3'] if isinstance(table_data['self_help']['teacher_eval3'], int) else 0,
                table_data['self_help']['parent_eval1'] if isinstance(table_data['self_help']['parent_eval1'], int) else 0,
                table_data['self_help']['parent_eval2'] if isinstance(table_data['self_help']['parent_eval2'], int) else 0,
                table_data['self_help']['parent_eval3'] if isinstance(table_data['self_help']['parent_eval3'], int) else 0
            ]),
            'receptive': sum([
                table_data['receptive']['teacher_eval1'] if isinstance(table_data['receptive']['teacher_eval1'], int) else 0,
                table_data['receptive']['teacher_eval2'] if isinstance(table_data['receptive']['teacher_eval2'], int) else 0,
                table_data['receptive']['teacher_eval3'] if isinstance(table_data['receptive']['teacher_eval3'], int) else 0
            ]),
            'expressive': sum([
                table_data['expressive']['teacher_eval1'] if isinstance(table_data['expressive']['teacher_eval1'], int) else 0,
                table_data['expressive']['teacher_eval2'] if isinstance(table_data['expressive']['teacher_eval2'], int) else 0,
                table_data['expressive']['teacher_eval3'] if isinstance(table_data['expressive']['teacher_eval3'], int) else 0,
                table_data['expressive']['parent_eval1'] if isinstance(table_data['expressive']['parent_eval1'], int) else 0,
                table_data['expressive']['parent_eval2'] if isinstance(table_data['expressive']['parent_eval2'], int) else 0,
                table_data['expressive']['parent_eval3'] if isinstance(table_data['expressive']['parent_eval3'], int) else 0
            ]),
            'cognitive': sum([
                table_data['cognitive']['teacher_eval1'] if isinstance(table_data['cognitive']['teacher_eval1'], int) else 0,
                table_data['cognitive']['teacher_eval2'] if isinstance(table_data['cognitive']['teacher_eval2'], int) else 0,
                table_data['cognitive']['teacher_eval3'] if isinstance(table_data['cognitive']['teacher_eval3'], int) else 0,
                table_data['cognitive']['parent_eval1'] if isinstance(table_data['cognitive']['parent_eval1'], int) else 0,
                table_data['cognitive']['parent_eval2'] if isinstance(table_data['cognitive']['parent_eval2'], int) else 0,
                table_data['cognitive']['parent_eval3'] if isinstance(table_data['cognitive']['parent_eval3'], int) else 0
            ]),
            'social': sum([
                table_data['social']['parent_eval1'] if isinstance(table_data['social']['parent_eval1'], int) else 0,
                table_data['social']['parent_eval2'] if isinstance(table_data['social']['parent_eval2'], int) else 0,
                table_data['social']['parent_eval3'] if isinstance(table_data['social']['parent_eval3'], int) else 0
            ])
        }
        
        return JsonResponse({
            'status': 'success',
            'student_name': student_name,
            'table_data': table_data,
            'chart_data': chart_data,
            'totals': totals
        })
        
    except Exception as e:
        import traceback
        print(f"Error in get_student_performance_data view: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'status': 'error',
            'message': f"An error occurred: {str(e)}"
        }, status=500)

@login_required
def upload_pdf(request):
    """
    Handle the PDF file upload.
    """
    if request.method == 'POST' and request.FILES.get('pdf_file'):
        pdf_files = request.FILES.getlist('pdf_file')
        
        for pdf_file in pdf_files:
            # Create a new PDFFile instance
            from .models import PDFFile
            pdf = PDFFile(
                name=pdf_file.name,
                file=pdf_file,
                size=pdf_file.size
            )
            pdf.save()
        
        messages.success(request, f'{len(pdf_files)} PDF file(s) uploaded successfully.')
        return redirect('pdf_view')
    
    messages.error(request, 'No PDF files were uploaded.')
    return redirect('pdf_view')

@login_required
def delete_pdf(request, pdf_id):
    """
    Delete a PDF file.
    """
    from .models import PDFFile
    
    try:
        pdf = PDFFile.objects.get(id=pdf_id)
        pdf.file.delete()  # Delete the actual file
        pdf.delete()       # Delete the database record
        messages.success(request, f'File "{pdf.name}" deleted successfully.')
    except PDFFile.DoesNotExist:
        messages.error(request, 'File not found.')
    
    return redirect('pdf_view')

@login_required
def manage_student_session(request):
    """
    View function to allow users to manage student session numbers.
    Parents can update their child's session number.
    Teachers can update any student's session number.
    """
    user = request.user
    success_message = None
    error_message = None
    student = None
    all_students = None
    
    # Check if user is a student
    student = Student.objects.filter(username=user.username).first()
    
    # If user is staff, get all students for management
    if user.is_staff:
        all_students = Student.objects.all().order_by('child_name')
    
    if request.method == 'POST':
        # Check if we're updating a specific student (teacher view)
        student_id = request.POST.get('student_id')
        session_no = int(request.POST.get('session_no', 1))
        
        if session_no < 1 or session_no > 3:
            error_message = "Session number must be between 1 and 3."
        else:
            if student_id:
                # Update a specific student (teacher only)
                if user.is_staff:
                    try:
                        target_student = Student.objects.get(id=student_id)
                        target_student.session_no = session_no
                        target_student.save()
                        success_message = f"Session updated for {target_student.child_name}."
                    except Student.DoesNotExist:
                        error_message = "Student not found."
                else:
                    error_message = "You do not have permission to update other students."
            else:
                # Update the logged-in user's student record
                if student:
                    student.session_no = session_no
                    student.save()
                    success_message = "Your session has been updated successfully."
                else:
                    error_message = "No student profile found for your account."
    
    context = {
        'user': user,
        'student': student,
        'all_students': all_students,
        'is_staff': user.is_staff,
        'success_message': success_message,
        'error_message': error_message,
    }
    
    return render(request, 'manage_student_session.html', context)

@login_required
def account_settings(request):
    """
    Enhanced view function for account settings with a modern interface.
    Allows users to change their username and password with real-time validation.
    """
    user = request.user
    success_message = None
    error_message = None
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'change_username':
            new_username = request.POST.get('new_username')
            
            # Check if username already exists
            if User.objects.filter(username=new_username).exists():
                error_message = "Username already exists. Please choose another one."
            else:
                # If the user is a student, update both User and Student models
                student = Student.objects.filter(username=user.username).first()
                if student:
                    student.username = new_username
                    student.save()
                
                # Update auth user
                user.username = new_username
                user.save()
                success_message = "Username updated successfully!"
                
        elif action == 'change_password':
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            # Verify current password
            if not user.check_password(current_password):
                error_message = "Current password is incorrect."
            elif new_password != confirm_password:
                error_message = "New passwords do not match."
            elif len(new_password) < 8:
                error_message = "Password must be at least 8 characters long."
            else:
                # Set new password
                user.set_password(new_password)
                user.save()
                
                # If user is a student, update Student model too
                student = Student.objects.filter(username=user.username).first()
                if student:
                    student.password = new_password
                    student.save()
                
                success_message = "Password updated successfully! Please log in again."
                logout(request)
                return redirect('login')
    
    context = {
        'user': user,
        'success_message': success_message,
        'error_message': error_message,
    }
    
    return render(request, 'account_settings.html', context)

def forgot_password(request):
    """
    View function to handle forgotten password requests.
    Users can reset their password by providing their username.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validate inputs
        if not username:
            return render(request, 'forgot_password.html', {'error': 'Please enter your username'})
        
        if not new_password or not confirm_password:
            return render(request, 'forgot_password.html', 
                         {'error': 'Please enter and confirm your new password',
                          'username': username})
        
        if new_password != confirm_password:
            return render(request, 'forgot_password.html', 
                         {'error': 'Passwords do not match',
                          'username': username})
        
        if len(new_password) < 8:
            return render(request, 'forgot_password.html', 
                         {'error': 'Password must be at least 8 characters long',
                          'username': username})
        
        # Check if user exists
        user = User.objects.filter(username=username).first()
        if not user:
            return render(request, 'forgot_password.html', 
                         {'error': 'No account found with that username'})
        
        # Update the password in the Django User model
        user.set_password(new_password)
        user.save()
        
        # If user is a student, update Student model too
        student = Student.objects.filter(username=username).first()
        if student:
            # Store the plaintext password in Student model for direct login
            student.password = new_password
            student.save()
        
        # Redirect to login page with success message
        messages.success(request, 'Password has been reset successfully. Please log in with your new password.')
        return redirect('login')
    
    return render(request, 'forgot_password.html')

@login_required
def create_announcement(request):
    """
    View function for creating announcements.
    If method is GET, displays the announcement form.
    If method is POST, processes the announcement submission.
    """
    # Check if user has permission to create announcements (staff only)
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to create announcements.")
        return redirect('dashboard')
    
    # Get all announcements for display
    announcements = Announcement.objects.all().order_by('-created_at')[:10]  # Show 10 most recent
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        
        # Validate form data
        if not title or not content:
            messages.error(request, "Please fill in both title and content fields.")
            return render(request, 'create_announcement.html', {'announcements': announcements})
        
        # Create new announcement
        announcement = Announcement(
            title=title,
            content=content,
            created_by=request.user
        )
        announcement.save()
        
        messages.success(request, "Announcement created successfully!")
        return redirect('create_announcement')
    
    # GET request - display the form
    return render(request, 'create_announcement.html', {'announcements': announcements})

@login_required
def view_announcements(request):
    """
    View function to display all active announcements.
    """
    announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'view_announcements.html', {'announcements': announcements})

@login_required
def delete_announcement(request, announcement_id):
    """
    View function to delete an announcement.
    Only staff members can delete announcements.
    """
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to delete announcements.")
        return redirect('view_announcements')
    
    announcement = get_object_or_404(Announcement, id=announcement_id)
    announcement.delete()
    
    messages.success(request, "Announcement deleted successfully!")
    return redirect('create_announcement')

@login_required
def generate_gross_motor_pdf(request):
    """
    Generate a PDF for the Gross Motor evaluation and save it to the database.
    Uses the dedicated GrossMotorPDF model to store the PDF directly.
    """
    if request.method == 'POST':
        try:
            # Extract form data
            student_name = request.POST.get('student_name', '')
            eval1_score = int(request.POST.get('eval1_score', 0))
            eval2_score = int(request.POST.get('eval2_score', 0))
            eval3_score = int(request.POST.get('eval3_score', 0))
            comments_json = request.POST.get('comments', '[]')
            comments = json.loads(comments_json)
            
            # Print debug info
            print(f"Starting PDF generation for {student_name}")
            print(f"Scores: {eval1_score}, {eval2_score}, {eval3_score}")
            print(f"Comments: {comments}")
            
            # Get checkbox data if provided
            checkbox_data_json = request.POST.get('checkbox_data', '[]')
            checkbox_data = json.loads(checkbox_data_json)
            print(f"Checkbox data: {checkbox_data}")
            
            # Create BytesIO buffer to receive PDF data
            buffer = BytesIO()
            print("Created BytesIO buffer")
            
            try:
                # Create a simple PDF instead of the complex table
                try:
                    from django.conf import settings
                    os.makedirs(os.path.join(settings.MEDIA_ROOT, 'gross_motor_pdfs'), exist_ok=True)
                    
                    # Create a PDF using ReportLab
                    # Use landscape orientation for more space
                    doc = SimpleDocTemplate(
                        buffer, 
                        pagesize=landscape(letter),
                        topMargin=30,
                        leftMargin=30,
                        rightMargin=30,
                        bottomMargin=30
                    )
                    elements = []
                    
                    # Define styles with enhanced formatting
                    styles = getSampleStyleSheet()
                    title_style = ParagraphStyle(
                        'Title',
                        parent=styles['Heading1'],
                        fontSize=18,
                        textColor=colors.darkgreen,
                        alignment=1,  # Center
                        spaceAfter=10
                    )
                    subtitle_style = ParagraphStyle(
                        'Subtitle',
                        parent=styles['Heading2'],
                        fontSize=14,
                        textColor=colors.darkgreen,
                        alignment=1,  # Center
                        spaceAfter=6
                    )
                    normal_style = ParagraphStyle(
                        'Normal',
                        parent=styles['Normal'],
                        fontSize=11,
                        leading=14,  # Line spacing
                        spaceBefore=6,
                        spaceAfter=6
                    )
                    header_style = ParagraphStyle(
                        'TableHeader',
                        parent=styles['Normal'],
                        fontSize=11,
                        textColor=colors.white,
                        alignment=1,  # Center
                        fontName='Helvetica-Bold'
                    )
                    cell_style = ParagraphStyle(
                        'TableCell',
                        parent=styles['Normal'],
                        fontSize=10,
                        leading=14,
                        wordWrap='CJK'  # Better word wrapping
                    )
                    
                    # Add title
                    elements.append(Paragraph(f"Gross Motor Evaluation", title_style))
                    elements.append(Spacer(1, 5))
                    elements.append(Paragraph(f"Student: {student_name}", subtitle_style))
                    elements.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", normal_style))
                    elements.append(Spacer(1, 15))
                    
                    # Helper function to create paragraphs for table cells
                    def create_cell_paragraph(text, style=cell_style):
                        return Paragraph(text, style)
                    
                    # Process checkbox data
                    def get_checkbox_status(checkbox_data, row_idx, col_idx):
                        if checkbox_data and len(checkbox_data) > row_idx and checkbox_data[row_idx]['checked'][col_idx]:
                            return "✓"
                        return ""
                    
                    # Get comments text
                    def get_comment(comments, number):
                        comment = next((c['text'] for c in comments if c['number'] == number), '')
                        if comment:
                            return comment
                        return "No comment"
                    
                    # Create table data with Paragraph objects for proper text wrapping
                    data = [
                        [
                            create_cell_paragraph("Gross Motor", header_style),
                            create_cell_paragraph("Material / Procedure", header_style),
                            create_cell_paragraph("1st Eval", header_style),
                            create_cell_paragraph("2nd Eval", header_style),
                            create_cell_paragraph("3rd Eval", header_style),
                            create_cell_paragraph("Comments", header_style)
                        ],
                        [
                            create_cell_paragraph("1. Climbs on the chair or other elevated furniture like a bed without a help"),
                            create_cell_paragraph("Parental report will suffice."),
                            create_cell_paragraph(get_checkbox_status(checkbox_data, 0, 0)),
                            create_cell_paragraph(get_checkbox_status(checkbox_data, 0, 1)),
                            create_cell_paragraph(get_checkbox_status(checkbox_data, 0, 2)),
                            create_cell_paragraph(get_comment(comments, 1))
                        ],
                        [
                            create_cell_paragraph("2. Walks downstairs, 2 feet on each step, with one handheld"),
                            create_cell_paragraph("MATERIAL: toy\nPROCEDURE: Ask the child to walk backwards by demonstrating this. Credit if the child is able to walk backwards without falling and holding anything. Parental report will suffice."),
                            create_cell_paragraph(get_checkbox_status(checkbox_data, 1, 0)),
                            create_cell_paragraph(get_checkbox_status(checkbox_data, 1, 1)),
                            create_cell_paragraph(get_checkbox_status(checkbox_data, 1, 2)),
                            create_cell_paragraph(get_comment(comments, 2))
                        ],
                        [
                            create_cell_paragraph("3. Dances patterns/joins group movement activities"),
                            create_cell_paragraph("MATERIAL: ball\nPROCEDURE: Encourage the child to run by rolling a ball across the floor. Credit if the child can run past and without tripping or falling."),
                            create_cell_paragraph(get_checkbox_status(checkbox_data, 2, 0)),
                            create_cell_paragraph(get_checkbox_status(checkbox_data, 2, 1)),
                            create_cell_paragraph(get_checkbox_status(checkbox_data, 2, 2)),
                            create_cell_paragraph(get_comment(comments, 3))
                        ],
                        [
                            create_cell_paragraph("TOTAL SCORE", ParagraphStyle('Total', parent=cell_style, fontName='Helvetica-Bold')),
                            create_cell_paragraph(""),
                            create_cell_paragraph(str(eval1_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                            create_cell_paragraph(str(eval2_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                            create_cell_paragraph(str(eval3_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                            create_cell_paragraph("")
                        ]
                    ]
                    
                    # Define column widths proportionally to the page width
                    col_widths = [120, 180, 45, 45, 45, 160]
                    
                    # Create the table with better spacing
                    table = Table(data, colWidths=col_widths, rowHeights=[30, 60, 80, 80, 30])
                    print("Created table for PDF")
                    
                    # Enhanced table style with better borders and colors
                    green_color = colors.Color(0.176, 0.416, 0.31)  # #2d6a4f in RGB
                    light_green = colors.Color(0.925, 0.965, 0.945)  # Light green for alternating rows
                    
                    table_style = TableStyle([
                        # Header row styling
                        ('BACKGROUND', (0, 0), (5, 0), green_color),
                        ('TEXTCOLOR', (0, 0), (5, 0), colors.white),
                        ('ALIGN', (0, 0), (5, 0), 'CENTER'),
                        ('VALIGN', (0, 0), (5, 0), 'MIDDLE'),
                        
                        # Alternating row colors
                        ('BACKGROUND', (0, 1), (5, 1), light_green),
                        ('BACKGROUND', (0, 3), (5, 3), light_green),
                        
                        # Total row styling
                        ('BACKGROUND', (0, 4), (5, 4), colors.Color(0.9, 0.9, 0.9)),
                        ('SPAN', (0, 4), (1, 4)),  # Span TOTAL SCORE across two columns
                        
                        # Vertical alignment
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        
                        # Text alignment
                        ('ALIGN', (2, 1), (4, 4), 'CENTER'),  # Center-align evaluation checkboxes
                        
                        # Borders
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('BOX', (0, 0), (-1, -1), 2, colors.black),
                        
                        # Cell padding
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('LEFTPADDING', (0, 0), (-1, -1), 8),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ])
                    
                    # Apply the style to the table
                    table.setStyle(table_style)
                    
                    # Add the table to the elements
                    elements.append(table)
                    
                    # Add a footer with disclaimer and signature line
                    elements.append(Spacer(1, 20))
                    elements.append(Paragraph("Disclaimer: This evaluation is based on observation and assessment at the time of evaluation.", normal_style))
                    
                    # Add a signature line
                    elements.append(Spacer(1, 30))
                    signature_data = [
                        ['________________________', '________________________'],
                        ['Evaluator\'s Signature', 'Date']
                    ]
                    signature_table = Table(signature_data, colWidths=[200, 200])
                    signature_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('TOPPADDING', (0, 1), (-1, 1), 5),
                        ('LINEABOVE', (0, 1), (0, 1), 1, colors.black),
                        ('LINEABOVE', (1, 1), (1, 1), 1, colors.black),
                    ]))
                    elements.append(signature_table)
                    
                    # Build the PDF with enhanced elements
                    print("Building PDF document...")
                    doc.build(elements)
                    print("PDF document built successfully")
                    
                    # Get the PDF value from the buffer
                    pdf_value = buffer.getvalue()
                    print(f"PDF size: {len(pdf_value)} bytes")
                    buffer.close()
                except Exception as complex_pdf_error:
                    print(f"Error creating complex PDF: {complex_pdf_error}")
                    # Fallback to simple PDF if complex one fails
                    buffer = BytesIO()  # Reset buffer
                    p = canvas.Canvas(buffer, pagesize=letter)
                    p.setFont("Helvetica-Bold", 16)
                    p.drawString(100, 750, f"Gross Motor Evaluation")
                    p.setFont("Helvetica", 12)
                    p.drawString(100, 730, f"Student: {student_name}")
                    p.drawString(100, 710, f"Date: {datetime.now().strftime('%B %d, %Y')}")
                    p.drawString(100, 670, f"1st Evaluation Score: {eval1_score}")
                    p.drawString(100, 650, f"2nd Evaluation Score: {eval2_score}")
                    p.drawString(100, 630, f"3rd Evaluation Score: {eval3_score}")
                    p.save()
                    pdf_value = buffer.getvalue()
                    buffer.close()
            except Exception as pdf_error:
                print(f"Error creating PDF content: {pdf_error}")
                import traceback
                traceback.print_exc()
                return JsonResponse({
                    'status': 'error',
                    'message': f'Error creating PDF content: {str(pdf_error)}'
                }, status=500)
            
            try:
                # Generate a unique filename
                filename = f"gross_motor_{student_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                db_info = []  # To store database operation info
                
                # Check if we already have a recent evaluation for this student
                from django.db.models import Q
                existing_record = GrossMotorPDF.objects.filter(
                    Q(student_name=student_name) & 
                    Q(uploaded_at__date=timezone.now().date())
                ).first()
                
                # If there's an existing evaluation from today, update it instead of creating a new one
                if existing_record:
                    print(f"Found existing GrossMotorPDF from today: {existing_record.id}")
                    db_info.append(f"Found existing GrossMotorPDF ID: {existing_record.id}")
                    
                    # Delete the old file
                    existing_record.file.delete(save=False)
                    
                    # Update the record with new data
                    existing_record.eval1_score = eval1_score
                    existing_record.eval2_score = eval2_score
                    existing_record.eval3_score = eval3_score
                    existing_record.file.save(filename, ContentFile(pdf_value))
                    existing_record.save()
                    
                    print(f"Updated existing GrossMotorPDF with ID: {existing_record.id}")
                    db_info.append(f"Updated existing GrossMotorPDF ID: {existing_record.id}")
                    gross_motor_pdf = existing_record
                else:
                    # Create a new GrossMotorPDF entry directly
                    gross_motor_pdf = GrossMotorPDF(
                        student_name=student_name,
                        eval1_score=eval1_score,
                        eval2_score=eval2_score,
                        eval3_score=eval3_score
                    )
                    gross_motor_pdf.file.save(filename, ContentFile(pdf_value))
                    gross_motor_pdf.save()
                    
                    print(f"Created new GrossMotorPDF with ID: {gross_motor_pdf.id}")
                    db_info.append(f"Created new GrossMotorPDF ID: {gross_motor_pdf.id}")
                
                # Also save to ParentGrossEvaluation for backward compatibility
                evaluation, created = ParentGrossEvaluation.objects.update_or_create(
                    student_name=student_name,
                    defaults={
                        'eval1_score': eval1_score,
                        'eval2_score': eval2_score,
                        'eval3_score': eval3_score
                    }
                )
                db_info.append(f"{'Created' if created else 'Updated'} ParentGrossEvaluation ID: {evaluation.id}")
                
                # Try getting the URL from the FileField
                pdf_url = gross_motor_pdf.file.url
                print(f"PDF URL from FileField: {pdf_url}")
                
                # Count existing records for confirmation
                gross_motor_pdf_count = GrossMotorPDF.objects.count()
                eval_count = ParentGrossEvaluation.objects.count()
                
                db_info.append(f"Total GrossMotorPDF records: {gross_motor_pdf_count}")
                db_info.append(f"Total ParentGrossEvaluation records: {eval_count}")
                
                # Return success response with PDF info
                return JsonResponse({
                    'status': 'success',
                    'message': 'Evaluation saved and PDF generated successfully',
                    'pdf_id': gross_motor_pdf.id,
                    'pdf_url': pdf_url,
                    'download_url': request.build_absolute_uri(pdf_url),
                    'db_operations': db_info,
                    'database_status': 'Records saved successfully to GrossMotorPDF model'
                })
            except Exception as db_error:
                print(f"Error saving PDF to database: {db_error}")
                import traceback
                traceback.print_exc()
                return JsonResponse({
                    'status': 'error',
                    'message': f'Error saving PDF to database: {str(db_error)}'
                }, status=500)
            
        except Exception as e:
            print(f"General error in generate_gross_motor_pdf: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'status': 'error',
                'message': f'Error generating PDF: {str(e)}'
            }, status=500)
            
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method. POST required.'
    }, status=405)

@login_required
def download_pdf(request, pdf_id):
    """
    Directly serve a PDF file by ID
    """
    try:
        pdf_file = PDFFile.objects.get(id=pdf_id)
        
        # Check if the file exists
        import os
        from django.conf import settings
        file_path = os.path.join(settings.MEDIA_ROOT, pdf_file.file.name)
        
        if not os.path.exists(file_path):
            print(f"PDF file not found at: {file_path}")
            return JsonResponse({'error': 'PDF file not found on disk'}, status=404)
        
        # Serve the file directly
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{os.path.basename(pdf_file.file.name)}"'
            return response
            
    except PDFFile.DoesNotExist:
        return JsonResponse({'error': 'PDF not found'}, status=404)
    except Exception as e:
        print(f"Error serving PDF: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def test_pdf(request):
    """A simple test view to check if PDF generation and saving works."""
    from reportlab.pdfgen import canvas
    from io import BytesIO
    import os
    from django.conf import settings
    import datetime
    
    try:
        # First, create the PDF in memory
        buffer = BytesIO()
        p = canvas.Canvas(buffer)
        p.drawString(100, 800, "Test PDF Generated Successfully")
        p.drawString(100, 780, f"Generated at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        p.drawString(100, 760, f"Generated by: {request.user.username}")
        p.showPage()
        p.save()
        
        # Get the value of the BytesIO buffer
        pdf_value = buffer.getvalue()
        buffer.close()
        
        # Create pdfs directory if it doesn't exist
        pdf_dir = os.path.join(settings.MEDIA_ROOT, 'pdfs')
        print(f"PDF directory: {pdf_dir}")
        try:
            os.makedirs(pdf_dir, exist_ok=True)
            print(f"PDF directory created/confirmed: {pdf_dir}")
        except Exception as dir_error:
            print(f"Error creating PDF directory: {dir_error}")
            # Try a different approach
            try:
                os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
                if not os.path.exists(pdf_dir):
                    os.mkdir(pdf_dir)
                print("PDF directory created using alternative method")
            except Exception as alt_error:
                print(f"Alternative directory creation failed: {alt_error}")
        
        # Check if directory exists now
        if os.path.exists(pdf_dir):
            print(f"PDF directory exists at: {pdf_dir}")
        else:
            print(f"WARNING: PDF directory does not exist at: {pdf_dir}")
            
        # Save the PDF to a file
        filename = f"test_pdf_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(pdf_dir, filename)
        print(f"Saving PDF to file: {filepath}")
        
        with open(filepath, 'wb') as f:
            f.write(pdf_value)
        
        # Return a simple HTML response
        return HttpResponse(f"""
        <html>
            <head><title>PDF Test</title></head>
            <body>
                <h1>PDF Generated Successfully!</h1>
                <p>PDF saved as: {filename}</p>
                <p>Full path: {filepath}</p>
                <p><a href="/media/pdfs/{filename}" target="_blank">View PDF</a></p>
                <p><a href="/system/dashboard/">Return to Dashboard</a></p>
            </body>
        </html>
        """)
    
    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        return HttpResponse(f"""
        <html>
            <head><title>PDF Test Failed</title></head>
            <body>
                <h1>PDF Generation Failed</h1>
                <p>Error: {str(e)}</p>
                <pre>{trace}</pre>
                <p><a href="/system/dashboard/">Return to Dashboard</a></p>
            </body>
        </html>
        """)

@login_required
def view_gross_motor_pdfs(request):
    """
    View function to list all gross motor PDFs.
    """
    gross_motor_pdfs = GrossMotorPDF.objects.all().order_by('-uploaded_at')
    return render(request, 'gross_motor_pdfs.html', {'pdfs': gross_motor_pdfs})

@login_required
def download_gross_motor_pdf(request, pdf_id):
    """
    Directly serve a gross motor PDF file by ID
    """
    try:
        pdf = GrossMotorPDF.objects.get(id=pdf_id)
        
        # Check if the file exists
        import os
        from django.conf import settings
        file_path = os.path.join(settings.MEDIA_ROOT, pdf.file.name)
        
        if not os.path.exists(file_path):
            print(f"PDF file not found at: {file_path}")
            return JsonResponse({'error': 'PDF file not found on disk'}, status=404)
        
        # Serve the file directly
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{os.path.basename(pdf.file.name)}"'
            return response
            
    except GrossMotorPDF.DoesNotExist:
        return JsonResponse({'error': 'PDF not found'}, status=404)
    except Exception as e:
        print(f"Error serving PDF: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def generate_self_help_pdf(request):
    """
    Generate a PDF for the Self-Help evaluation and save it to the database.
    Uses the dedicated SelfHelpPDF model to store the PDF directly.
    """
    if request.method == 'POST':
        try:
            # Extract form data
            student_name = request.POST.get('student_name', '')
            eval1_score = int(request.POST.get('eval1_score', 0))
            eval2_score = int(request.POST.get('eval2_score', 0))
            eval3_score = int(request.POST.get('eval3_score', 0))
            comments_json = request.POST.get('comments', '[]')
            comments = json.loads(comments_json)
            
            # Print debug info
            print(f"Starting PDF generation for {student_name}")
            print(f"Scores: {eval1_score}, {eval2_score}, {eval3_score}")
            print(f"Comments: {comments}")
            
            # Get checkbox data if provided
            checkbox_data_json = request.POST.get('checkbox_data', '[]')
            checkbox_data = json.loads(checkbox_data_json)
            print(f"Checkbox data: {checkbox_data}")
            
            # Create BytesIO buffer to receive PDF data
            buffer = BytesIO()
            print("Created BytesIO buffer")
            
            try:
                # Create a simple PDF instead of the complex table
                try:
                    from django.conf import settings
                    os.makedirs(os.path.join(settings.MEDIA_ROOT, 'self_help_pdfs'), exist_ok=True)
                    
                    # Create a PDF using ReportLab
                    # Use landscape orientation for more space
                    doc = SimpleDocTemplate(
                        buffer, 
                        pagesize=landscape(letter),
                        topMargin=30,
                        leftMargin=30,
                        rightMargin=30,
                        bottomMargin=30
                    )
                    elements = []
                    
                    # Define styles with enhanced formatting
                    styles = getSampleStyleSheet()
                    title_style = ParagraphStyle(
                        'Title',
                        parent=styles['Heading1'],
                        fontSize=18,
                        textColor=colors.darkgreen,
                        alignment=1,  # Center
                        spaceAfter=10
                    )
                    subtitle_style = ParagraphStyle(
                        'Subtitle',
                        parent=styles['Heading2'],
                        fontSize=14,
                        textColor=colors.darkgreen,
                        alignment=1,  # Center
                        spaceAfter=6
                    )
                    normal_style = ParagraphStyle(
                        'Normal',
                        parent=styles['Normal'],
                        fontSize=11,
                        leading=14,  # Line spacing
                        spaceBefore=6,
                        spaceAfter=6
                    )
                    header_style = ParagraphStyle(
                        'TableHeader',
                        parent=styles['Normal'],
                        fontSize=11,
                        textColor=colors.white,
                        alignment=1,  # Center
                        fontName='Helvetica-Bold'
                    )
                    cell_style = ParagraphStyle(
                        'TableCell',
                        parent=styles['Normal'],
                        fontSize=10,
                        leading=14,
                        wordWrap='CJK'  # Better word wrapping
                    )
                    
                    # Add title
                    elements.append(Paragraph(f"Self-Help Evaluation", title_style))
                    elements.append(Spacer(1, 5))
                    elements.append(Paragraph(f"Student: {student_name}", subtitle_style))
                    elements.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", normal_style))
                    elements.append(Spacer(1, 15))
                    
                    # Helper function to create paragraphs for table cells
                    def create_cell_paragraph(text, style=cell_style):
                        return Paragraph(text, style)
                    
                    # Process checkbox data
                    def get_checkbox_status(checkbox_data, row_idx, col_idx):
                        if checkbox_data and len(checkbox_data) > row_idx and checkbox_data[row_idx]['checked'][col_idx]:
                            return "✓"
                        return ""
                    
                    # Get comments text
                    def get_comment(comments, number):
                        comment = next((c['text'] for c in comments if c['number'] == number), '')
                        if comment:
                            return comment
                        return "No comment"
                    
                    # Self-Help evaluation items
                    self_help_items = [
                        ["1. Feeding sub-domain", "Parental report will suffice."],
                        ["2. Feed self using fingers to eat non-hands with spoon", "Automatically credit if child eats without spillage. Parental report will suffice."],
                        ["3. Feed self using spoon without spillage", "Automatically credit if child eats without spillage. Parental report will suffice."],
                        ["4. Feed self using fingers without spillage", "Parental report will suffice."],
                        ["5. Feed self using spoon without spillage", "Parental report will suffice."],
                        ["6. Eats with head held for spoon-feeding during any meal", "Parental report will suffice."],
                        ["7. Gets drink for self-unassisted", "Parental report will suffice."],
                        ["8. Pours from pitcher without spillage", "Parental report will suffice."],
                        ["9. Volunteers to help younger siblings/family members when no adult is around", "Parental report will suffice."],
                        ["10. Dressing sub-domain\nSelf-dresses after being dressed (e.g., raises arms or lift legs)", "Parental report will suffice."],
                        ["11. Pulls down preferred short pants", "Parental report will suffice."],
                        ["12. Removes sando", "Parental report will suffice."],
                        ["13. Dresses without assistance except for buttoning and tying", "Parental report will suffice."],
                        ["14. Toilet Training sub-domain\nInforms adult only after he has already urinated (wash) or moved has bowels (pooped) in his underpants", "Parental report will suffice."],
                        ["15. Informs the adult of need to urinate (pee) or move bowels (poop) ahead of time such as through place (e.g., comfort room)", "Parental report will suffice."],
                        ["16. Goes to the designated place to urinate (pee) or move bowels (poop) but sometimes still does this in his underpants", "Parental report will suffice."],
                        ["17. Goes to the designated place to urinate (pee) or move bowels (poop) and never does this in his underpants", "Parental report will suffice."],
                        ["18. Wipes/cleans self after a bowel movement (poop)", "Parental report will suffice."],
                        ["19. Bathing sub-domain\nParticipates when bathing (e.g., putting on soap)", "Parental report will suffice."],
                        ["20. Bathes without any help", "Parental report will suffice."]
                    ]
                    
                    # Create table header
                    data = [[
                        create_cell_paragraph("Self-Help", header_style),
                        create_cell_paragraph("Material/Procedure", header_style),
                        create_cell_paragraph("1st Eval", header_style),
                        create_cell_paragraph("2nd Eval", header_style),
                        create_cell_paragraph("3rd Eval", header_style),
                        create_cell_paragraph("Comments", header_style)
                    ]]
                    
                    # Add rows for each evaluation item
                    for i, (item_text, procedure_text) in enumerate(self_help_items):
                        data.append([
                            create_cell_paragraph(item_text),
                            create_cell_paragraph(procedure_text),
                            create_cell_paragraph(get_checkbox_status(checkbox_data, i, 0)),
                            create_cell_paragraph(get_checkbox_status(checkbox_data, i, 1)),
                            create_cell_paragraph(get_checkbox_status(checkbox_data, i, 2)),
                            create_cell_paragraph(get_comment(comments, i+1))
                        ])
                    
                    # Add total row
                    data.append([
                        create_cell_paragraph("TOTAL SCORE", ParagraphStyle('Total', parent=cell_style, fontName='Helvetica-Bold')),
                        create_cell_paragraph(""),
                        create_cell_paragraph(str(eval1_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                        create_cell_paragraph(str(eval2_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                        create_cell_paragraph(str(eval3_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                        create_cell_paragraph("")
                    ])
                    
                    # Define column widths proportionally to the page width
                    col_widths = [140, 180, 45, 45, 45, 140]
                    
                    # Calculate row heights based on content (with minimums)
                    row_heights = [30]  # Header row
                    for i in range(len(self_help_items)):
                        # Determine height based on content length
                        row_heights.append(max(30, min(20 + len(self_help_items[i][0]) // 3, 60)))
                    row_heights.append(30)  # Total row
                    
                    # Create the table with better spacing
                    table = Table(data, colWidths=col_widths, rowHeights=row_heights)
                    print("Created table for PDF")
                    
                    # Enhanced table style with better borders and colors
                    green_color = colors.Color(0.176, 0.416, 0.31)  # #2d6a4f in RGB
                    light_green = colors.Color(0.925, 0.965, 0.945)  # Light green for alternating rows
                    
                    table_style = TableStyle([
                        # Header row styling
                        ('BACKGROUND', (0, 0), (5, 0), green_color),
                        ('TEXTCOLOR', (0, 0), (5, 0), colors.white),
                        ('ALIGN', (0, 0), (5, 0), 'CENTER'),
                        ('VALIGN', (0, 0), (5, 0), 'MIDDLE'),
                        
                        # Alternating row colors
                        ('BACKGROUND', (0, 1), (5, 1), light_green),
                        ('BACKGROUND', (0, 3), (5, 3), light_green),
                        ('BACKGROUND', (0, 5), (5, 5), light_green),
                        ('BACKGROUND', (0, 7), (5, 7), light_green),
                        ('BACKGROUND', (0, 9), (5, 9), light_green),
                        ('BACKGROUND', (0, 11), (5, 11), light_green),
                        ('BACKGROUND', (0, 13), (5, 13), light_green),
                        ('BACKGROUND', (0, 15), (5, 15), light_green),
                        ('BACKGROUND', (0, 17), (5, 17), light_green),
                        ('BACKGROUND', (0, 19), (5, 19), light_green),
                        
                        # Total row styling
                        ('BACKGROUND', (0, -1), (5, -1), colors.Color(0.9, 0.9, 0.9)),
                        ('SPAN', (0, -1), (1, -1)),  # Span TOTAL SCORE across two columns
                        
                        # Vertical alignment
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        
                        # Text alignment
                        ('ALIGN', (2, 1), (4, -1), 'CENTER'),  # Center-align evaluation checkboxes
                        
                        # Borders
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('BOX', (0, 0), (-1, -1), 2, colors.black),
                        
                        # Cell padding
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('LEFTPADDING', (0, 0), (-1, -1), 8),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ])
                    
                    # Apply the style to the table
                    table.setStyle(table_style)
                    
                    # Add the table to the elements
                    elements.append(table)
                    
                    # Add a footer with disclaimer and signature line
                    elements.append(Spacer(1, 20))
                    elements.append(Paragraph("Disclaimer: This evaluation is based on observation and assessment at the time of evaluation.", normal_style))
                    
                    # Add a signature line
                    elements.append(Spacer(1, 30))
                    signature_data = [
                        ['________________________', '________________________'],
                        ['Evaluator\'s Signature', 'Date']
                    ]
                    signature_table = Table(signature_data, colWidths=[200, 200])
                    signature_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('TOPPADDING', (0, 1), (-1, 1), 5),
                        ('LINEABOVE', (0, 1), (0, 1), 1, colors.black),
                        ('LINEABOVE', (1, 1), (1, 1), 1, colors.black),
                    ]))
                    elements.append(signature_table)
                    
                    # Build the PDF with enhanced elements
                    print("Building PDF document...")
                    doc.build(elements)
                    print("PDF document built successfully")
                    
                    # Get the PDF value from the buffer
                    pdf_value = buffer.getvalue()
                    print(f"PDF size: {len(pdf_value)} bytes")
                    buffer.close()
                except Exception as complex_pdf_error:
                    print(f"Error creating complex PDF: {complex_pdf_error}")
                    # Fallback to simple PDF if complex one fails
                    buffer = BytesIO()  # Reset buffer
                    p = canvas.Canvas(buffer, pagesize=letter)
                    p.setFont("Helvetica-Bold", 16)
                    p.drawString(100, 750, f"Self-Help Evaluation")
                    p.setFont("Helvetica", 12)
                    p.drawString(100, 730, f"Student: {student_name}")
                    p.drawString(100, 710, f"Date: {datetime.now().strftime('%B %d, %Y')}")
                    p.drawString(100, 670, f"1st Evaluation Score: {eval1_score}")
                    p.drawString(100, 650, f"2nd Evaluation Score: {eval2_score}")
                    p.drawString(100, 630, f"3rd Evaluation Score: {eval3_score}")
                    p.save()
                    pdf_value = buffer.getvalue()
                    buffer.close()
            except Exception as pdf_error:
                print(f"Error creating PDF content: {pdf_error}")
                import traceback
                traceback.print_exc()
                return JsonResponse({
                    'status': 'error',
                    'message': f'Error creating PDF content: {str(pdf_error)}'
                }, status=500)
            
            try:
                # Generate a unique filename
                filename = f"self_help_{student_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                db_info = []  # To store database operation info
                
                # Check if we already have a recent evaluation for this student
                from django.db.models import Q
                existing_record = SelfHelpPDF.objects.filter(
                    Q(student_name=student_name) & 
                    Q(uploaded_at__date=timezone.now().date())
                ).first()
                
                # If there's an existing evaluation from today, update it instead of creating a new one
                if existing_record:
                    print(f"Found existing SelfHelpPDF from today: {existing_record.id}")
                    db_info.append(f"Found existing SelfHelpPDF ID: {existing_record.id}")
                    
                    # Delete the old file
                    existing_record.file.delete(save=False)
                    
                    # Update the record with new data
                    existing_record.eval1_score = eval1_score
                    existing_record.eval2_score = eval2_score
                    existing_record.eval3_score = eval3_score
                    existing_record.file.save(filename, ContentFile(pdf_value))
                    existing_record.save()
                    
                    print(f"Updated existing SelfHelpPDF with ID: {existing_record.id}")
                    db_info.append(f"Updated existing SelfHelpPDF ID: {existing_record.id}")
                    self_help_pdf = existing_record
                else:
                    # Create a new SelfHelpPDF entry directly
                    self_help_pdf = SelfHelpPDF(
                        student_name=student_name,
                        eval1_score=eval1_score,
                        eval2_score=eval2_score,
                        eval3_score=eval3_score
                    )
                    self_help_pdf.file.save(filename, ContentFile(pdf_value))
                    self_help_pdf.save()
                    
                    print(f"Created new SelfHelpPDF with ID: {self_help_pdf.id}")
                    db_info.append(f"Created new SelfHelpPDF ID: {self_help_pdf.id}")
                
                # Also save to ParentSelfHelpEvaluation for backward compatibility
                evaluation, created = ParentSelfHelpEvaluation.objects.update_or_create(
                    student_name=student_name,
                    defaults={
                        'eval1_score': eval1_score,
                        'eval2_score': eval2_score,
                        'eval3_score': eval3_score
                    }
                )
                db_info.append(f"{'Created' if created else 'Updated'} ParentSelfHelpEvaluation ID: {evaluation.id}")
                
                # Try getting the URL from the FileField
                pdf_url = self_help_pdf.file.url
                print(f"PDF URL from FileField: {pdf_url}")
                
                # Count existing records for confirmation
                self_help_pdf_count = SelfHelpPDF.objects.count()
                eval_count = ParentSelfHelpEvaluation.objects.count()
                
                db_info.append(f"Total SelfHelpPDF records: {self_help_pdf_count}")
                db_info.append(f"Total ParentSelfHelpEvaluation records: {eval_count}")
                
                # Return success response with PDF info
                return JsonResponse({
                    'status': 'success',
                    'message': 'Self-Help evaluation PDF generated successfully',
                    'pdf_id': self_help_pdf.id,
                    'pdf_url': pdf_url,
                    'download_url': request.build_absolute_uri(pdf_url),
                    'db_operations': db_info,
                    'database_status': 'Records saved successfully to database'
                })
            except Exception as db_error:
                print(f"Error saving PDF to database: {db_error}")
                import traceback
                traceback.print_exc()
                return JsonResponse({
                    'status': 'error',
                    'message': f'Error saving PDF to database: {str(db_error)}'
                }, status=500)
            
        except Exception as e:
            print(f"General error in generate_self_help_pdf: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'status': 'error',
                'message': f'Error generating PDF: {str(e)}'
            }, status=500)
            
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method. POST required.'
    }, status=405)

@login_required
def download_self_help_pdf(request, pdf_id):
    """
    Download a specific Self-Help PDF file by its ID.
    """
    try:
        pdf = get_object_or_404(SelfHelpPDF, id=pdf_id)
        response = FileResponse(pdf.file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="self_help_evaluation_{pdf.student_name}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f"Error downloading PDF: {str(e)}")
        return redirect('dashboard')

@login_required
def view_self_help_pdfs(request):
    """
    View all Self-Help PDF files.
    """
    pdfs = SelfHelpPDF.objects.all().order_by('-uploaded_at')
    return render(request, 'pdfs/self_help_pdfs.html', {'pdfs': pdfs})

@login_required
def generate_social_pdf(request):
    """
    Generate a PDF for the Social-Emotional evaluation and save it to the database.
    Uses the dedicated SocialPDF model to store the PDF directly.
    """
    if request.method == 'POST':
        try:
            # Extract form data
            student_name = request.POST.get('student_name', '')
            eval1_score = int(request.POST.get('eval1_score', 0))
            eval2_score = int(request.POST.get('eval2_score', 0))
            eval3_score = int(request.POST.get('eval3_score', 0))
            comments_json = request.POST.get('comments', '[]')
            comments = json.loads(comments_json)
            
            # Print debug info
            print(f"Starting PDF generation for {student_name}")
            print(f"Scores: {eval1_score}, {eval2_score}, {eval3_score}")
            print(f"Comments: {comments}")
            
            # Get checkbox data if provided
            checkbox_data_json = request.POST.get('checkbox_data', '[]')
            checkbox_data = json.loads(checkbox_data_json)
            print(f"Checkbox data: {checkbox_data}")
            
            # Create BytesIO buffer to receive PDF data
            buffer = BytesIO()
            print("Created BytesIO buffer")
            
            try:
                # Create a simple PDF instead of the complex table
                try:
                    from django.conf import settings
                    os.makedirs(os.path.join(settings.MEDIA_ROOT, 'social_pdfs'), exist_ok=True)
                    
                    # Create a PDF using ReportLab
                    # Use landscape orientation for more space
                    doc = SimpleDocTemplate(
                        buffer, 
                        pagesize=landscape(letter),
                        topMargin=30,
                        leftMargin=30,
                        rightMargin=30,
                        bottomMargin=30
                    )
                    elements = []
                    
                    # Define styles with enhanced formatting
                    styles = getSampleStyleSheet()
                    title_style = ParagraphStyle(
                        'Title',
                        parent=styles['Heading1'],
                        fontSize=18,
                        textColor=colors.darkgreen,
                        alignment=1,  # Center
                        spaceAfter=10
                    )
                    subtitle_style = ParagraphStyle(
                        'Subtitle',
                        parent=styles['Heading2'],
                        fontSize=14,
                        textColor=colors.darkgreen,
                        alignment=1,  # Center
                        spaceAfter=6
                    )
                    normal_style = ParagraphStyle(
                        'Normal',
                        parent=styles['Normal'],
                        fontSize=11,
                        leading=14,  # Line spacing
                        spaceBefore=6,
                        spaceAfter=6
                    )
                    header_style = ParagraphStyle(
                        'TableHeader',
                        parent=styles['Normal'],
                        fontSize=11,
                        textColor=colors.white,
                        alignment=1,  # Center
                        fontName='Helvetica-Bold'
                    )
                    cell_style = ParagraphStyle(
                        'TableCell',
                        parent=styles['Normal'],
                        fontSize=10,
                        leading=14,
                        wordWrap='CJK'  # Better word wrapping
                    )
                    
                    # Add title
                    elements.append(Paragraph(f"Social-Emotional Evaluation", title_style))
                    elements.append(Spacer(1, 5))
                    elements.append(Paragraph(f"Student: {student_name}", subtitle_style))
                    elements.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", normal_style))
                    elements.append(Spacer(1, 15))
                    
                    # Helper function to create paragraphs for table cells
                    def create_cell_paragraph(text, style=cell_style):
                        return Paragraph(text, style)
                    
                    # Process checkbox data
                    def get_checkbox_status(checkbox_data, row_idx, col_idx):
                        if checkbox_data and len(checkbox_data) > row_idx and checkbox_data[row_idx]['checked'][col_idx]:
                            return "✓"
                        return ""
                    
                    # Get comments text
                    def get_comment(comments, number):
                        comment = next((c['text'] for c in comments if c['number'] == number), '')
                        if comment:
                            return comment
                        return "No comment"
                    
                    # Social-Emotional evaluation items
                    social_items = [
                        ["1. Responds to adult activities or nearby children", "Parental report will suffice."],
                        ["2. Begins to recognize differences in emotions", "Parental report will suffice."],
                        ["3. Plays alone but likes to be near adults or brothers and sisters", "Parental report will suffice."],
                        ["4. Laughs or squeals about happy things", "Parental report will suffice."],
                        ["5. Uses speech-like babbling", "Parental report will suffice."],
                        ["7. Gets and interpretively into a sequence correctly", "Parental report will suffice."],
                        ["8. Hugs or cuddles toys, companions, parents", "Parental report will suffice."],
                        ["9. Demonstrates respect for others' belongings and space", "Parental report will suffice."],
                        ["10. Shows with pictures 'sad' and 'happy'", "Parental report will suffice."],
                        ["11. Shares toys with others (e.g., cooking, pababa)", "Parental report will suffice."],
                        ["12. Identifies feelings in others", "Credit if the child can tell when the examiner is sad or hurt. Parental report will suffice."],
                        ["13. Appropriately uses words referring to mental states (e.g., know, think, etc.)", "Parental report will suffice."],
                        ["14. Tolerates feelings in others", "Parental report will suffice."],
                        ["15. Reacts when toys with a problem or someone to his wants", "Credit if the child tries to solve the problem instead of crying when something doesn't go his way (e.g., attempting a toy with his reasons). Parental report will suffice."],
                        ["16. Helps the family chores (e.g., sweeping floors, watering plants, etc.)", "Parental report will suffice."],
                        ["18. Curious about environment but knows when to stop asking questions of adults", "Credit if the child asks questions about things around him but knows when to stop asking if a topic. Parental report will suffice."],
                        ["19. Ask permission to play with his being used by another", "Parental report will suffice."],
                        ["20. Defends possessions with determination", "Credit if the child tries to hold on to what is his when someone tries to grab him. Parental report will suffice."],
                        ["21. Helps organize group play", "Parental report will suffice."],
                        ["22. Can talk about complex feelings (e.g., anger, sadness, worry); he experiences", "Parental report will suffice."],
                        ["23. Cooperates with peers (e.g., plays outside only after school)", "Parental report will suffice."],
                        ["24. Interacts well with adults/siblings/family members", "Parental report will suffice."]
                    ]
                    
                    # Create table header
                    data = [[
                        create_cell_paragraph("Social-Emotional", header_style),
                        create_cell_paragraph("Material/Procedure", header_style),
                        create_cell_paragraph("1st Eval", header_style),
                        create_cell_paragraph("2nd Eval", header_style),
                        create_cell_paragraph("3rd Eval", header_style),
                        create_cell_paragraph("Comments", header_style)
                    ]]
                    
                    # Add rows for each evaluation item
                    for i, (item_text, procedure_text) in enumerate(social_items):
                        data.append([
                            create_cell_paragraph(item_text),
                            create_cell_paragraph(procedure_text),
                            create_cell_paragraph(get_checkbox_status(checkbox_data, i, 0)),
                            create_cell_paragraph(get_checkbox_status(checkbox_data, i, 1)),
                            create_cell_paragraph(get_checkbox_status(checkbox_data, i, 2)),
                            create_cell_paragraph(get_comment(comments, i+1))
                        ])
                    
                    # Add total row
                    data.append([
                        create_cell_paragraph("TOTAL SCORE", ParagraphStyle('Total', parent=cell_style, fontName='Helvetica-Bold')),
                        create_cell_paragraph(""),
                        create_cell_paragraph(str(eval1_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                        create_cell_paragraph(str(eval2_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                        create_cell_paragraph(str(eval3_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                        create_cell_paragraph("")
                    ])
                    
                    # Define column widths proportionally to the page width
                    col_widths = [140, 180, 45, 45, 45, 140]
                    
                    # Calculate row heights based on content (with minimums)
                    row_heights = [30]  # Header row
                    for i in range(len(social_items)):
                        # Determine height based on content length
                        row_heights.append(max(30, min(20 + len(social_items[i][0]) // 3, 60)))
                    row_heights.append(30)  # Total row
                    
                    # Create the table with better spacing
                    table = Table(data, colWidths=col_widths, rowHeights=row_heights)
                    print("Created table for PDF")
                    
                    # Enhanced table style with better borders and colors
                    green_color = colors.Color(0.176, 0.416, 0.31)  # #2d6a4f in RGB
                    light_green = colors.Color(0.925, 0.965, 0.945)  # Light green for alternating rows
                    
                    table_style = TableStyle([
                        # Header row styling
                        ('BACKGROUND', (0, 0), (5, 0), green_color),
                        ('TEXTCOLOR', (0, 0), (5, 0), colors.white),
                        ('ALIGN', (0, 0), (5, 0), 'CENTER'),
                        ('VALIGN', (0, 0), (5, 0), 'MIDDLE'),
                        
                        # Alternating row colors
                        ('BACKGROUND', (0, 1), (5, 1), light_green),
                        ('BACKGROUND', (0, 3), (5, 3), light_green),
                        ('BACKGROUND', (0, 5), (5, 5), light_green),
                        ('BACKGROUND', (0, 7), (5, 7), light_green),
                        ('BACKGROUND', (0, 9), (5, 9), light_green),
                        ('BACKGROUND', (0, 11), (5, 11), light_green),
                        ('BACKGROUND', (0, 13), (5, 13), light_green),
                        ('BACKGROUND', (0, 15), (5, 15), light_green),
                        ('BACKGROUND', (0, 17), (5, 17), light_green),
                        ('BACKGROUND', (0, 19), (5, 19), light_green),
                        ('BACKGROUND', (0, 21), (5, 21), light_green),
                        
                        # Total row styling
                        ('BACKGROUND', (0, -1), (5, -1), colors.Color(0.9, 0.9, 0.9)),
                        ('SPAN', (0, -1), (1, -1)),  # Span TOTAL SCORE across two columns
                        
                        # Vertical alignment
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        
                        # Text alignment
                        ('ALIGN', (2, 1), (4, -1), 'CENTER'),  # Center-align evaluation checkboxes
                        
                        # Borders
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('BOX', (0, 0), (-1, -1), 2, colors.black),
                        
                        # Cell padding
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('LEFTPADDING', (0, 0), (-1, -1), 8),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ])
                    
                    # Apply the style to the table
                    table.setStyle(table_style)
                    
                    # Add the table to the elements
                    elements.append(table)
                    
                    # Add a footer with disclaimer and signature line
                    elements.append(Spacer(1, 20))
                    elements.append(Paragraph("Disclaimer: This evaluation is based on observation and assessment at the time of evaluation.", normal_style))
                    
                    # Add a signature line
                    elements.append(Spacer(1, 30))
                    signature_data = [
                        ['________________________', '________________________'],
                        ['Evaluator\'s Signature', 'Date']
                    ]
                    signature_table = Table(signature_data, colWidths=[200, 200])
                    signature_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('TOPPADDING', (0, 1), (-1, 1), 5),
                        ('LINEABOVE', (0, 1), (0, 1), 1, colors.black),
                        ('LINEABOVE', (1, 1), (1, 1), 1, colors.black),
                    ]))
                    elements.append(signature_table)
                    
                    # Build the PDF with enhanced elements
                    print("Building PDF document...")
                    doc.build(elements)
                    print("PDF document built successfully")
                    
                    # Get the PDF value from the buffer
                    pdf_value = buffer.getvalue()
                    print(f"PDF size: {len(pdf_value)} bytes")
                    buffer.close()
                except Exception as complex_pdf_error:
                    print(f"Error creating complex PDF: {complex_pdf_error}")
                    # Fallback to simple PDF if complex one fails
                    buffer = BytesIO()  # Reset buffer
                    p = canvas.Canvas(buffer, pagesize=letter)
                    p.setFont("Helvetica-Bold", 16)
                    p.drawString(100, 750, f"Social-Emotional Evaluation")
                    p.setFont("Helvetica", 12)
                    p.drawString(100, 730, f"Student: {student_name}")
                    p.drawString(100, 710, f"Date: {datetime.now().strftime('%B %d, %Y')}")
                    p.drawString(100, 670, f"1st Evaluation Score: {eval1_score}")
                    p.drawString(100, 650, f"2nd Evaluation Score: {eval2_score}")
                    p.drawString(100, 630, f"3rd Evaluation Score: {eval3_score}")
                    p.save()
                    pdf_value = buffer.getvalue()
                    buffer.close()
            except Exception as pdf_error:
                print(f"Error creating PDF content: {pdf_error}")
                import traceback
                traceback.print_exc()
                return JsonResponse({
                    'status': 'error',
                    'message': f'Error creating PDF content: {str(pdf_error)}'
                }, status=500)
            
            try:
                # Generate a unique filename
                filename = f"social_{student_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                db_info = []  # To store database operation info
                
                # Check if we already have a recent evaluation for this student
                from django.db.models import Q
                existing_record = SocialPDF.objects.filter(
                    Q(student_name=student_name) & 
                    Q(uploaded_at__date=timezone.now().date())
                ).first()
                
                # If there's an existing evaluation from today, update it instead of creating a new one
                if existing_record:
                    print(f"Found existing SocialPDF from today: {existing_record.id}")
                    db_info.append(f"Found existing SocialPDF ID: {existing_record.id}")
                    
                    # Delete the old file
                    existing_record.file.delete(save=False)
                    
                    # Update the record with new data
                    existing_record.eval1_score = eval1_score
                    existing_record.eval2_score = eval2_score
                    existing_record.eval3_score = eval3_score
                    existing_record.file.save(filename, ContentFile(pdf_value))
                    existing_record.save()
                    
                    print(f"Updated existing SocialPDF with ID: {existing_record.id}")
                    db_info.append(f"Updated existing SocialPDF ID: {existing_record.id}")
                    social_pdf = existing_record
                else:
                    # Create a new SocialPDF entry directly
                    social_pdf = SocialPDF(
                        student_name=student_name,
                        eval1_score=eval1_score,
                        eval2_score=eval2_score,
                        eval3_score=eval3_score
                    )
                    social_pdf.file.save(filename, ContentFile(pdf_value))
                    social_pdf.save()
                    
                    print(f"Created new SocialPDF with ID: {social_pdf.id}")
                    db_info.append(f"Created new SocialPDF ID: {social_pdf.id}")
                
                # Also save to ParentSocialEvaluation for backward compatibility
                try:
                    # First try to get the most recent evaluation for this student
                    parent_eval = ParentSocialEvaluation.objects.filter(
                        student_name=student_name
                    ).order_by('-created_at').first()
                    
                    if parent_eval:
                        # Update existing record
                        parent_eval.eval1_score = eval1_score
                        parent_eval.eval2_score = eval2_score
                        parent_eval.eval3_score = eval3_score
                        parent_eval.save()
                        db_info.append(f"Updated existing ParentSocialEvaluation ID: {parent_eval.id}")
                    else:
                        # Create new record
                        parent_eval = ParentSocialEvaluation.objects.create(
                            student_name=student_name,
                            eval1_score=eval1_score,
                            eval2_score=eval2_score,
                            eval3_score=eval3_score
                        )
                        db_info.append(f"Created new ParentSocialEvaluation ID: {parent_eval.id}")
                except Exception as e:
                    print(f"Warning: Error updating ParentSocialEvaluation: {e}")
                    db_info.append(f"Warning: Error updating ParentSocialEvaluation: {str(e)}")
                    # Continue execution, don't fail the whole operation
                
                # Try getting the URL from the FileField
                pdf_url = social_pdf.file.url
                print(f"PDF URL from FileField: {pdf_url}")
                
                # Count existing records for confirmation
                social_pdf_count = SocialPDF.objects.count()
                eval_count = ParentSocialEvaluation.objects.count()
                
                db_info.append(f"Total SocialPDF records: {social_pdf_count}")
                db_info.append(f"Total ParentSocialEvaluation records: {eval_count}")
                
                # Return success response with PDF info
                return JsonResponse({
                    'status': 'success',
                    'message': 'Social-Emotional evaluation PDF generated successfully',
                    'pdf_id': social_pdf.id,
                    'pdf_url': pdf_url,
                    'download_url': request.build_absolute_uri(pdf_url),
                    'db_operations': db_info,
                    'database_status': 'Records saved successfully to database'
                })
            except Exception as db_error:
                print(f"Error saving PDF to database: {db_error}")
                import traceback
                traceback.print_exc()
                return JsonResponse({
                    'status': 'error',
                    'message': f'Error saving PDF to database: {str(db_error)}'
                }, status=500)
            
        except Exception as e:
            print(f"General error in generate_social_pdf: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'status': 'error',
                'message': f'Error generating PDF: {str(e)}'
            }, status=500)
            
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method. POST required.'
    }, status=405)

@login_required
def download_social_pdf(request, pdf_id):
    """
    Download a specific Social-Emotional PDF file by its ID.
    """
    try:
        pdf = get_object_or_404(SocialPDF, id=pdf_id)
        response = FileResponse(pdf.file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="social_evaluation_{pdf.student_name}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f"Error downloading PDF: {str(e)}")
        return redirect('dashboard')

@login_required
def view_social_pdfs(request):
    """
    View all Social-Emotional PDF files.
    """
    pdfs = SocialPDF.objects.all().order_by('-uploaded_at')
    return render(request, 'pdfs/social_pdfs.html', {'pdfs': pdfs})

@login_required
def generate_expressive_pdf(request):
    """
    Generate a PDF for the Expressive Language evaluation and save it to the database.
    Uses the dedicated ExpressivePDF model to store the PDF directly.
    """
    if request.method == 'POST':
        try:
            # Extract form data
            student_name = request.POST.get('student_name', '')
            eval1_score = int(request.POST.get('eval1_score', 0))
            eval2_score = int(request.POST.get('eval2_score', 0))
            eval3_score = int(request.POST.get('eval3_score', 0))
            comments_json = request.POST.get('comments', '[]')
            comments = json.loads(comments_json)
            
            # Print debug info
            print(f"Starting PDF generation for {student_name}")
            print(f"Scores: {eval1_score}, {eval2_score}, {eval3_score}")
            print(f"Comments: {comments}")
            
            # Get checkbox data if provided
            checkbox_data_json = request.POST.get('checkbox_data', '[]')
            checkbox_data = json.loads(checkbox_data_json)
            print(f"Checkbox data: {checkbox_data}")
            
            # Create BytesIO buffer to receive PDF data
            buffer = BytesIO()
            print("Created BytesIO buffer")
            
            try:
                # Create a simple PDF instead of the complex table
                try:
                    from django.conf import settings
                    os.makedirs(os.path.join(settings.MEDIA_ROOT, 'expressive_pdfs'), exist_ok=True)
                    
                    # Create a PDF using ReportLab
                    # Use landscape orientation for more space
                    doc = SimpleDocTemplate(
                        buffer, 
                        pagesize=landscape(letter),
                        topMargin=30,
                        leftMargin=30,
                        rightMargin=30,
                        bottomMargin=30
                    )
                    elements = []
                    
                    # Define styles with enhanced formatting
                    styles = getSampleStyleSheet()
                    title_style = ParagraphStyle(
                        'Title',
                        parent=styles['Heading1'],
                        fontSize=18,
                        textColor=colors.darkgreen,
                        alignment=1,  # Center
                        spaceAfter=10
                    )
                    subtitle_style = ParagraphStyle(
                        'Subtitle',
                        parent=styles['Heading2'],
                        fontSize=14,
                        textColor=colors.darkgreen,
                        alignment=1,  # Center
                        spaceAfter=6
                    )
                    normal_style = ParagraphStyle(
                        'Normal',
                        parent=styles['Normal'],
                        fontSize=11,
                        leading=14,  # Line spacing
                        spaceBefore=6,
                        spaceAfter=6
                    )
                    header_style = ParagraphStyle(
                        'TableHeader',
                        parent=styles['Normal'],
                        fontSize=11,
                        textColor=colors.white,
                        alignment=1,  # Center
                        fontName='Helvetica-Bold'
                    )
                    cell_style = ParagraphStyle(
                        'TableCell',
                        parent=styles['Normal'],
                        fontSize=10,
                        leading=14,
                        wordWrap='CJK'  # Better word wrapping
                    )
                    
                    # Add title
                    elements.append(Paragraph(f"Expressive Language Evaluation", title_style))
                    elements.append(Spacer(1, 5))
                    elements.append(Paragraph(f"Student: {student_name}", subtitle_style))
                    elements.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", normal_style))
                    elements.append(Spacer(1, 15))
                    
                    # Helper function to create paragraphs for table cells
                    def create_cell_paragraph(text, style=cell_style):
                        return Paragraph(text, style)
                    
                    # Process checkbox data
                    def get_checkbox_status(checkbox_data, row_idx, col_idx):
                        if checkbox_data and len(checkbox_data) > row_idx and checkbox_data[row_idx]['checked'][col_idx]:
                            return "✓"
                        return ""
                    
                    # Get comments text
                    def get_comment(comments, number):
                        comment = next((c['text'] for c in comments if c['number'] == number), '')
                        if comment:
                            return comment
                        return "No comment"
                    
                    # Expressive Language evaluation items
                    expressive_items = [
                        ["1. Uses pronouns (e.g., I, me, ako, akin)", "Parental report will suffice."],
                        ["2. Uses 2-to-3-word verb-noun combination (e.g., sipa patas)", "Parental report will suffice."],
                        ["3. Speaks in grammatically correct 2- to 3-word sentences", "Parental report will suffice."],
                        ["4. Ask 'what' questions", "Parental report will suffice."],
                        ["5. Ask 'who' and 'why' questions", "Parental report will suffice."]
                    ]
                    
                    # Create table header
                    data = [[
                        create_cell_paragraph("Expressive Language", header_style),
                        create_cell_paragraph("Material/Procedure", header_style),
                        create_cell_paragraph("1st Eval", header_style),
                        create_cell_paragraph("2nd Eval", header_style),
                        create_cell_paragraph("3rd Eval", header_style),
                        create_cell_paragraph("Comments", header_style)
                    ]]
                    
                    # Add rows for each evaluation item
                    for i, (item_text, procedure_text) in enumerate(expressive_items):
                        data.append([
                            create_cell_paragraph(item_text),
                            create_cell_paragraph(procedure_text),
                            create_cell_paragraph(get_checkbox_status(checkbox_data, i, 0)),
                            create_cell_paragraph(get_checkbox_status(checkbox_data, i, 1)),
                            create_cell_paragraph(get_checkbox_status(checkbox_data, i, 2)),
                            create_cell_paragraph(get_comment(comments, i+1))
                        ])
                    
                    # Add total row
                    data.append([
                        create_cell_paragraph("TOTAL SCORE", ParagraphStyle('Total', parent=cell_style, fontName='Helvetica-Bold')),
                        create_cell_paragraph(""),
                        create_cell_paragraph(str(eval1_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                        create_cell_paragraph(str(eval2_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                        create_cell_paragraph(str(eval3_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                        create_cell_paragraph("")
                    ])
                    
                    # Define column widths proportionally to the page width
                    col_widths = [140, 180, 45, 45, 45, 140]
                    
                    # Calculate row heights based on content (with minimums)
                    row_heights = [30]  # Header row
                    for i in range(len(expressive_items)):
                        # Determine height based on content length
                        row_heights.append(max(30, min(20 + len(expressive_items[i][0]) // 3, 60)))
                    row_heights.append(30)  # Total row
                    
                    # Create the table with better spacing
                    table = Table(data, colWidths=col_widths, rowHeights=row_heights)
                    print("Created table for PDF")
                    
                    # Enhanced table style with better borders and colors
                    green_color = colors.Color(0.176, 0.416, 0.31)  # #2d6a4f in RGB
                    light_green = colors.Color(0.925, 0.965, 0.945)  # Light green for alternating rows
                    
                    table_style = TableStyle([
                        # Header row styling
                        ('BACKGROUND', (0, 0), (5, 0), green_color),
                        ('TEXTCOLOR', (0, 0), (5, 0), colors.white),
                        ('ALIGN', (0, 0), (5, 0), 'CENTER'),
                        ('VALIGN', (0, 0), (5, 0), 'MIDDLE'),
                        
                        # Alternating row colors
                        ('BACKGROUND', (0, 1), (5, 1), light_green),
                        ('BACKGROUND', (0, 3), (5, 3), light_green),
                        ('BACKGROUND', (0, 5), (5, 5), light_green),
                        
                        # Total row styling
                        ('BACKGROUND', (0, -1), (5, -1), colors.Color(0.9, 0.9, 0.9)),
                        ('SPAN', (0, -1), (1, -1)),  # Span TOTAL SCORE across two columns
                        
                        # Vertical alignment
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        
                        # Text alignment
                        ('ALIGN', (2, 1), (4, -1), 'CENTER'),  # Center-align evaluation checkboxes
                        
                        # Borders
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('BOX', (0, 0), (-1, -1), 2, colors.black),
                        
                        # Cell padding
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('LEFTPADDING', (0, 0), (-1, -1), 8),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ])
                    
                    # Apply the style to the table
                    table.setStyle(table_style)
                    
                    # Add the table to the elements
                    elements.append(table)
                    
                    # Add a footer with disclaimer and signature line
                    elements.append(Spacer(1, 20))
                    elements.append(Paragraph("Disclaimer: This evaluation is based on observation and assessment at the time of evaluation.", normal_style))
                    
                    # Add a signature line
                    elements.append(Spacer(1, 30))
                    signature_data = [
                        ['________________________', '________________________'],
                        ['Evaluator\'s Signature', 'Date']
                    ]
                    signature_table = Table(signature_data, colWidths=[200, 200])
                    signature_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('TOPPADDING', (0, 1), (-1, 1), 5),
                        ('LINEABOVE', (0, 1), (0, 1), 1, colors.black),
                        ('LINEABOVE', (1, 1), (1, 1), 1, colors.black),
                    ]))
                    elements.append(signature_table)
                    
                    # Build the PDF with enhanced elements
                    print("Building PDF document...")
                    doc.build(elements)
                    print("PDF document built successfully")
                    
                    # Get the PDF value from the buffer
                    pdf_value = buffer.getvalue()
                    print(f"PDF size: {len(pdf_value)} bytes")
                    buffer.close()
                except Exception as complex_pdf_error:
                    print(f"Error creating complex PDF: {complex_pdf_error}")
                    # Fallback to simple PDF if complex one fails
                    buffer = BytesIO()  # Reset buffer
                    p = canvas.Canvas(buffer, pagesize=letter)
                    p.setFont("Helvetica-Bold", 16)
                    p.drawString(100, 750, f"Expressive Language Evaluation")
                    p.setFont("Helvetica", 12)
                    p.drawString(100, 730, f"Student: {student_name}")
                    p.drawString(100, 710, f"Date: {datetime.now().strftime('%B %d, %Y')}")
                    p.drawString(100, 670, f"1st Evaluation Score: {eval1_score}")
                    p.drawString(100, 650, f"2nd Evaluation Score: {eval2_score}")
                    p.drawString(100, 630, f"3rd Evaluation Score: {eval3_score}")
                    p.save()
                    pdf_value = buffer.getvalue()
                    buffer.close()
            except Exception as pdf_error:
                print(f"Error creating PDF content: {pdf_error}")
                import traceback
                traceback.print_exc()
                return JsonResponse({
                    'status': 'error',
                    'message': f'Error creating PDF content: {str(pdf_error)}'
                }, status=500)
            
            try:
                # Generate a unique filename
                filename = f"expressive_{student_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                db_info = []  # To store database operation info
                
                # Check if we already have a recent evaluation for this student
                from django.db.models import Q
                existing_record = ExpressivePDF.objects.filter(
                    Q(student_name=student_name) & 
                    Q(uploaded_at__date=timezone.now().date())
                ).first()
                
                # If there's an existing evaluation from today, update it instead of creating a new one
                if existing_record:
                    print(f"Found existing ExpressivePDF from today: {existing_record.id}")
                    db_info.append(f"Found existing ExpressivePDF ID: {existing_record.id}")
                    
                    # Delete the old file
                    existing_record.file.delete(save=False)
                    
                    # Update the record with new data
                    existing_record.eval1_score = eval1_score
                    existing_record.eval2_score = eval2_score
                    existing_record.eval3_score = eval3_score
                    existing_record.file.save(filename, ContentFile(pdf_value))
                    existing_record.save()
                    
                    print(f"Updated existing ExpressivePDF with ID: {existing_record.id}")
                    db_info.append(f"Updated existing ExpressivePDF ID: {existing_record.id}")
                    expressive_pdf = existing_record
                else:
                    # Create a new ExpressivePDF entry directly
                    expressive_pdf = ExpressivePDF(
                        student_name=student_name,
                        eval1_score=eval1_score,
                        eval2_score=eval2_score,
                        eval3_score=eval3_score
                    )
                    expressive_pdf.file.save(filename, ContentFile(pdf_value))
                    expressive_pdf.save()
                    
                    print(f"Created new ExpressivePDF with ID: {expressive_pdf.id}")
                    db_info.append(f"Created new ExpressivePDF ID: {expressive_pdf.id}")
                
                # Also save to ParentExpressiveEvaluation for backward compatibility
                try:
                    # First try to get the most recent evaluation for this student
                    parent_eval = ParentExpressiveEvaluation.objects.filter(
                        student_name=student_name
                    ).order_by('-created_at').first()
                    
                    if parent_eval:
                        # Update existing record
                        parent_eval.eval1_score = eval1_score
                        parent_eval.eval2_score = eval2_score
                        parent_eval.eval3_score = eval3_score
                        parent_eval.save()
                        db_info.append(f"Updated existing ParentExpressiveEvaluation ID: {parent_eval.id}")
                    else:
                        # Create new record
                        parent_eval = ParentExpressiveEvaluation.objects.create(
                            student_name=student_name,
                            eval1_score=eval1_score,
                            eval2_score=eval2_score,
                            eval3_score=eval3_score
                        )
                        db_info.append(f"Created new ParentExpressiveEvaluation ID: {parent_eval.id}")
                except Exception as e:
                    print(f"Warning: Error updating ParentExpressiveEvaluation: {e}")
                    db_info.append(f"Warning: Error updating ParentExpressiveEvaluation: {str(e)}")
                    # Continue execution, don't fail the whole operation
                
                # Try getting the URL from the FileField
                pdf_url = expressive_pdf.file.url
                print(f"PDF URL from FileField: {pdf_url}")
                
                # Count existing records for confirmation
                expressive_pdf_count = ExpressivePDF.objects.count()
                eval_count = ParentExpressiveEvaluation.objects.count()
                
                db_info.append(f"Total ExpressivePDF records: {expressive_pdf_count}")
                db_info.append(f"Total ParentExpressiveEvaluation records: {eval_count}")
                
                # Return success response with PDF info
                return JsonResponse({
                    'status': 'success',
                    'message': 'Expressive Language evaluation PDF generated successfully',
                    'pdf_id': expressive_pdf.id,
                    'pdf_url': pdf_url,
                    'download_url': request.build_absolute_uri(pdf_url),
                    'db_operations': db_info,
                    'database_status': 'Records saved successfully to database'
                })
            except Exception as db_error:
                print(f"Error saving PDF to database: {db_error}")
                import traceback
                traceback.print_exc()
                return JsonResponse({
                    'status': 'error',
                    'message': f'Error saving PDF to database: {str(db_error)}'
                }, status=500)
            
        except Exception as e:
            print(f"General error in generate_expressive_pdf: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'status': 'error',
                'message': f'Error generating PDF: {str(e)}'
            }, status=500)
            
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method. POST required.'
    }, status=405)

@login_required
def download_expressive_pdf(request, pdf_id):
    """
    Download a specific Expressive Language PDF file by its ID.
    """
    try:
        pdf = get_object_or_404(ExpressivePDF, id=pdf_id)
        response = FileResponse(pdf.file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="expressive_evaluation_{pdf.student_name}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f"Error downloading PDF: {str(e)}")
        return redirect('dashboard')

@login_required
def view_expressive_pdfs(request):
    """
    View all Expressive Language PDF files.
    """
    pdfs = ExpressivePDF.objects.all().order_by('-uploaded_at')
    return render(request, 'pdfs/expressive_pdfs.html', {'pdfs': pdfs})

@login_required
def generate_cognitive_pdf(request):
    """
    Generate a PDF for cognitive domain evaluation, and save it to the database.
    This function can be called independently or automatically from the form submission process.
    """
    try:
        # Get data from the request
        student_name = request.POST.get('student_name')
        eval1_score = int(request.POST.get('eval1_score', 0))
        eval2_score = int(request.POST.get('eval2_score', 0))
        eval3_score = int(request.POST.get('eval3_score', 0))
        comments_json = request.POST.get('comments', '[]')
        checkbox_data_json = request.POST.get('checkbox_data', '[]')
        
        comments = json.loads(comments_json) if comments_json else []
        checkbox_data = json.loads(checkbox_data_json) if checkbox_data_json else []
        
        print(f"Generating PDF for {student_name}, scores: {eval1_score}, {eval2_score}, {eval3_score}")
        
        try:
            # Prepare cognitive evaluation items
            cognitive_items = [
                ("1. Imitates house play just seen a few minutes earlier", "Parental report will suffice."),
                ("2. Gives an object but does not release it", "Parental report will suffice.")
            ]
            
            # Generate PDF using ReportLab
            buffer = BytesIO()
            
            # Try generating a complex, nicely formatted PDF
            try:
                doc = SimpleDocTemplate(
                    buffer,
                    pagesize=letter,
                    leftMargin=36,
                    rightMargin=36,
                    topMargin=36,
                    bottomMargin=36
                )
                
                styles = getSampleStyleSheet()
                elements = []
                
                # Create a custom style for the title
                title_style = ParagraphStyle(
                    'Title',
                    parent=styles['Heading1'],
                    fontSize=18,
                    textColor=colors.Color(0.176, 0.416, 0.31),  # Green color #2d6a4f
                    spaceAfter=10,
                    alignment=1  # Center alignment
                )
                
                # Add a title
                elements.append(Paragraph(f"Cognitive Domain Evaluation", title_style))
                
                # Add student name and date
                student_info_style = ParagraphStyle(
                    'StudentInfo',
                    parent=styles['Normal'],
                    fontSize=12,
                    spaceAfter=12,
                    alignment=1  # Center alignment
                )
                elements.append(Paragraph(f"Student: {student_name}", student_info_style))
                elements.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", student_info_style))
                
                # Add some space
                elements.append(Spacer(1, 20))
                
                # Define a style for table cells
                cell_style = ParagraphStyle(
                    'CellStyle',
                    parent=styles['Normal'],
                    fontSize=10,
                    leading=14,
                    wordWrap='CJK',
                )
                
                # Helper functions
                def create_cell_paragraph(text, style=cell_style):
                    return Paragraph(text, style)
                
                def get_checkbox_status(checkbox_data, row_idx, col_idx):
                    for item in checkbox_data:
                        if item.get('item') == row_idx + 1:
                            if item.get('checked', [])[col_idx]:
                                return "✓"
                    return ""
                
                def get_comment(comments, number):
                    for comment in comments:
                        if comment.get('number') == number or comment.get('item') == number:
                            return comment.get('text', '')
                    return ""
                
                # Create table data
                data = [
                    [
                        create_cell_paragraph("Cognitive", ParagraphStyle('Header', parent=cell_style, fontName='Helvetica-Bold', textColor=colors.white)),
                        create_cell_paragraph("Material/Procedure", ParagraphStyle('Header', parent=cell_style, fontName='Helvetica-Bold', textColor=colors.white)),
                        create_cell_paragraph("1st Eval", ParagraphStyle('Header', parent=cell_style, fontName='Helvetica-Bold', textColor=colors.white, alignment=1)),
                        create_cell_paragraph("2nd Eval", ParagraphStyle('Header', parent=cell_style, fontName='Helvetica-Bold', textColor=colors.white, alignment=1)),
                        create_cell_paragraph("3rd Eval", ParagraphStyle('Header', parent=cell_style, fontName='Helvetica-Bold', textColor=colors.white, alignment=1)),
                        create_cell_paragraph("Comments", ParagraphStyle('Header', parent=cell_style, fontName='Helvetica-Bold', textColor=colors.white))
                    ]
                ]
                
                # Add rows for each evaluation item
                for i, (item_text, procedure_text) in enumerate(cognitive_items):
                    data.append([
                        create_cell_paragraph(item_text),
                        create_cell_paragraph(procedure_text),
                        create_cell_paragraph(get_checkbox_status(checkbox_data, i, 0)),
                        create_cell_paragraph(get_checkbox_status(checkbox_data, i, 1)),
                        create_cell_paragraph(get_checkbox_status(checkbox_data, i, 2)),
                        create_cell_paragraph(get_comment(comments, i+1))
                    ])
                
                # Add total row
                data.append([
                    create_cell_paragraph("TOTAL SCORE", ParagraphStyle('Total', parent=cell_style, fontName='Helvetica-Bold')),
                    create_cell_paragraph(""),
                    create_cell_paragraph(str(eval1_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                    create_cell_paragraph(str(eval2_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                    create_cell_paragraph(str(eval3_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                    create_cell_paragraph("")
                ])
                
                # Define column widths proportionally to the page width
                col_widths = [140, 180, 45, 45, 45, 140]
                
                # Calculate row heights based on content (with minimums)
                row_heights = [30]  # Header row
                for i in range(len(cognitive_items)):
                    # Determine height based on content length
                    row_heights.append(max(30, min(20 + len(cognitive_items[i][0]) // 3, 60)))
                row_heights.append(30)  # Total row
                
                # Create the table with better spacing
                table = Table(data, colWidths=col_widths, rowHeights=row_heights)
                print("Created table for PDF")
                
                # Enhanced table style with better borders and colors
                green_color = colors.Color(0.176, 0.416, 0.31)  # #2d6a4f in RGB
                light_green = colors.Color(0.925, 0.965, 0.945)
                
                table_style = TableStyle([
                    # Header styling
                    ('BACKGROUND', (0, 0), (-1, 0), green_color),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    
                    # Borders
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BOX', (0, 0), (-1, -1), 1, colors.black),
                    
                    # Align evaluation checkboxes to center
                    ('ALIGN', (2, 1), (4, -2), 'CENTER'),
                    
                    # Style for total row
                    ('BACKGROUND', (0, -1), (-1, -1), light_green),
                    ('ALIGN', (0, -1), (0, -1), 'RIGHT'),
                ])
                
                table.setStyle(table_style)
                elements.append(table)
                
                # Build the PDF
                doc.build(elements)
                pdf_value = buffer.getvalue()
                print(f"PDF size: {len(pdf_value)} bytes")
                buffer.close()
            except Exception as complex_pdf_error:
                print(f"Error creating complex PDF: {complex_pdf_error}")
                # Fallback to simple PDF if complex one fails
                buffer = BytesIO()  # Reset buffer
                p = canvas.Canvas(buffer, pagesize=letter)
                p.setFont("Helvetica-Bold", 16)
                p.drawString(100, 750, f"Cognitive Evaluation")
                p.setFont("Helvetica", 12)
                p.drawString(100, 730, f"Student: {student_name}")
                p.drawString(100, 710, f"Date: {datetime.now().strftime('%B %d, %Y')}")
                p.drawString(100, 670, f"1st Evaluation Score: {eval1_score}")
                p.drawString(100, 650, f"2nd Evaluation Score: {eval2_score}")
                p.drawString(100, 630, f"3rd Evaluation Score: {eval3_score}")
                p.save()
                pdf_value = buffer.getvalue()
                buffer.close()
        except Exception as pdf_error:
            print(f"Error creating PDF content: {pdf_error}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'status': 'error',
                'message': f'Error creating PDF content: {str(pdf_error)}'
            }, status=500)
            
        # Save the PDF to the database
        try:
            # Create a filename for the PDF
            filename = f"cognitive_{student_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
            
            # Save to CognitivePDF model
            cognitive_pdf = CognitivePDF(
                student_name=student_name,
                file=ContentFile(pdf_value, name=filename),
                eval1_score=eval1_score,
                eval2_score=eval2_score,
                eval3_score=eval3_score
            )
            cognitive_pdf.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'PDF generated and saved successfully',
                'pdf_id': cognitive_pdf.id
            })
        except Exception as save_error:
            print(f"Error saving PDF: {save_error}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'status': 'error', 
                'message': f'Error saving PDF: {str(save_error)}'
            }, status=500)
    except Exception as e:
        print(f"Error in generate_cognitive_pdf: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'status': 'error', 
            'message': f'Error generating PDF: {str(e)}'
        }, status=500)

@login_required
def download_cognitive_pdf(request, pdf_id):
    """Download the cognitive PDF file"""
    try:
        pdf = get_object_or_404(CognitivePDF, id=pdf_id)
        filename = os.path.basename(pdf.file.name)
        response = FileResponse(pdf.file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        print(f"Error downloading PDF: {e}")
        raise Http404("PDF not found")

@login_required
def view_cognitive_pdfs(request):
    """View all cognitive PDF files"""
    pdfs = CognitivePDF.objects.all().order_by('-uploaded_at')
    return render(request, 'view_pdfs.html', {'pdfs': pdfs, 'domain': 'Cognitive'})

