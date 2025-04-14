from django.shortcuts import render, redirect, get_object_or_404
from .models import Student, StudentScore, EvaluationRecord, CognitiveEvaluation, ExpressiveEvaluation, FineEvaluation, GrossEvaluation, ReceptiveEvaluation, SelfHelpEvaluation, ParentSelfHelpEvaluation, ParentGrossEvaluation, ParentSocialEvaluation, ParentExpressiveEvaluation, ParentCognitiveEvaluation
from .forms import StudentForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect, csrf_exempt
import json
from django.db.models import Q
from django.utils import timezone
from datetime import date




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
        try:
            scores = student.scores
        except StudentScore.DoesNotExist:
            scores = None
        context = {
            'student': student,
            'scores': scores,
            'gross_evaluations': GrossEvaluation.objects.all(),
            'fine_evaluations': FineEvaluation.objects.all(),
            'self_help_evaluations': SelfHelpEvaluation.objects.all(),
            'expressive_evaluations': ExpressiveEvaluation.objects.all(),
            'receptive_evaluations': ReceptiveEvaluation.objects.all(),
            'cognitive_evaluations': CognitiveEvaluation.objects.all()
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
        
        return render(request, "TDash.html", {
            "students": students,
            "users_count": users_count,
            "evaluations_count": evaluations_count,
            "messages_count": 0  # You can replace this with actual message count if you have a message model
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
            
            messages.success(request, f'Student {request.POST.get("child_name")} has been successfully registered!')
            return redirect('performance')
            
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
                # Create Django user if it doesn't exist
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={'password': password}
                )
                
                # If user was retrieved but not created, update password
                if not created:
                    user.set_password(password)
                    user.save()
                
                # Login the user
                login(request, user)
                return redirect('dashboard')  # Redirect to dashboard
            else:
                messages.error(request, 'Invalid username or password')
                return render(request, 'Login.html', {'error': 'Invalid username or password'})
    
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


def settings_view(request):
    """
    View function for the settings page.
    """
    return render(request, 'settings.html')

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
def messages_view(request):
    """
    View function for the messages page.
    """
    return render(request, 'message.html')

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

