from .models import Student  # Adjust import if needed
from django.shortcuts import render, redirect
from django.db import transaction, IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import (
    Student,
    Announcement,
    Event,
    EditableEvaluationTable,
    EvaluationData,
    EvaluationDataTeacher,
    SchoolYear)
from .forms import StudentForm
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_protect, csrf_exempt
import json
from django.db.models import Q
from django.utils import timezone
from datetime import date
import os
from io import BytesIO
from datetime import datetime
from django.urls import reverse
import random
import string
import pytz
import traceback  # Add this import
from django.utils.timesince import timesince
from django.views.decorators.http import require_POST

def current_school_year(request):
    current_school_year = Student.get_current_school_year()
    return render(request, 'manage_student_session.html', {'current_school_year': current_school_year})


@login_required
def dashboard(request):
    # Get the logged-in user
    user = request.user
    print(f"Dashboard access - User: {user.username}, Email: {user.email}, Is staff: {user.is_staff}")

    if not user.is_staff:
        # This is a parent/student account
        student = Student.objects.filter(gmail=user.email).first()

        if not student:
            print(f"No student record found for email: {user.email}")
            messages.error(request, "No student record found for your account.")
            return redirect('login')

        print(f"Loading parent dashboard for student: {student.child_name}")

        # Get recent announcements for notifications
        recent_announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')[:3]

        context = {
            'student': student,
            'recent_announcements': recent_announcements
        }
        return render(request, "PDash.html", context)
    else:
        # This is a teacher/admin account
        print(f"Loading teacher dashboard")

        # Get all students and sort them by their evaluation scores
        students = list(Student.objects.all())
        # Sort students by their highest evaluation score
        students.sort(key=lambda x: max(
            x.get_total_evaluation_score()['eval3_total'],
            x.get_total_evaluation_score()['eval2_total'],
            x.get_total_evaluation_score()['eval1_total']
        ), reverse=True)
        
        # Get the total number of users
        total_users = User.objects.count()
        # Get total number of students
        total_students = Student.objects.count()
        

        # Get recent announcements for teacher dashboard
        recent_announcements = Announcement.objects.all().order_by('-created_at')[:5]

        return render(request, "TDash.html", {
            "students": students,
            "total_users": total_users,
            "total_students": total_students,
            "messages_count": 0,
            "recent_announcements": recent_announcements
        })


def add_student(request):
    if request.method == 'POST':
        try:
            email = request.POST.get('gmail')
            child_name = request.POST.get('child_name')

            print(f"Attempting to add student with email: {email}")

            if Student.objects.filter(gmail=email).exists():
                messages.error(
                    request,
                    f'A student with email {email} is already registered. Please use a different email.')
                return render(request, 'add_student.html')

            # Generate unique username from child's name
            base_username = child_name.replace(' ', '_').lower()
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1

            with transaction.atomic():
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        'username': username,
                        'is_staff': False,
                    }
                )

                if created:
                    random_password = ''.join(
                        random.choices(
                            string.ascii_letters +
                            string.digits,
                            k=10))
                    user.set_password(random_password)
                    user.save()
                    print(
                        f"Created Django user - Username: {username}, Email: {email}")
                else:
                    username = user.username  # Use existing username
                    print(
                        f"Using existing Django user - Username: {username}, Email: {email}")

                # Extra safety check before saving student
                if Student.objects.filter(gmail=email).exists():
                    messages.error(
                        request, f'A student with email {email} is already registered.')
                    return render(request, 'add_student.html')

                student = Student(
                    child_name=child_name,
                    sex=request.POST.get('sex'),
                    dob=request.POST.get('dob'),
                    handedness=request.POST.get('handedness'),
                    studying=request.POST.get('studying'),
                    birth_order=request.POST.get('birth_order'),
                    num_siblings=int(request.POST.get('num_siblings')),
                    lrn=request.POST.get('lrn'),  # Add LRN field

                    # Address info
                    address=request.POST.get('address'),
                    barangay=request.POST.get('barangay'),
                    municipality=request.POST.get('municipality'),
                    province=request.POST.get('province'),
                    region=request.POST.get('region'),

                    # Father's info
                    father_name=request.POST.get('father_name'),
                    father_age=int(request.POST.get('father_age')),
                    father_occupation=request.POST.get('father_occupation'),
                    father_education=request.POST.get('father_education'),

                    # Mother's info
                    mother_name=request.POST.get('mother_name'),
                    mother_age=int(request.POST.get('mother_age')),
                    mother_occupation=request.POST.get('mother_occupation'),
                    mother_education=request.POST.get('mother_education'),

                    gmail=email,
                    username=username
                )

                student.save()
                print(f"Created student record for: {student.child_name}")

            # Success message
            if created:
                messages.success(
                    request,
                    f'Student registered successfully. Credentials sent to {email}. Username: {username}')
            else:
                messages.success(
                    request,
                    f'Student registered successfully. The parent can log in with their existing account.')

            return redirect('add_student')

        except IntegrityError as e:
            print(f"IntegrityError: {str(e)}")
            messages.error(
                request, 'This email has already been used. Please try again.')
            return render(request, 'add_student.html')

        except Exception as e:
            print(f"Error adding student: {str(e)}")
            messages.error(request, f'Error registering student: {str(e)}')
            return render(request, 'add_student.html')
    return render(request, 'add_student.html')


def edit_student(request):
    if request.method == 'GET':
        try:
            student_name = request.GET.get('name')
            student = get_object_or_404(Student, child_name=student_name)
            
            # Return student data as JSON
            return JsonResponse({
                'child_name': student.child_name,
                'sex': student.sex,
                'dob': student.dob.strftime('%Y-%m-%d') if student.dob else '',
                'handedness': student.handedness,
                'studying': student.studying,
                'birth_order': student.birth_order,
                'num_siblings': student.num_siblings,
                'father_name': student.father_name,
                'father_age': student.father_age,
                'father_occupation': student.father_occupation,
                'father_education': student.father_education,
                'mother_name': student.mother_name,
                'mother_age': student.mother_age,
                'mother_occupation': student.mother_occupation,
                'mother_education': student.mother_education,
                'address': student.address,
                'barangay': student.barangay,
                'municipality': student.municipality,
                'province': student.province,
                'region': student.region,
                'gmail': student.gmail,
                'username': student.username,
                'status': 'success'
            })
        except Student.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': f'Student not found: {student_name}'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
            
    elif request.method == 'POST':
        try:
            student_name = request.POST.get('student_name')  # Changed from student_id
            student = get_object_or_404(Student, child_name=student_name)  # Changed from id to child_name
            print(f"Attempting to edit student: {student.child_name}")

            # Update student information
            student.child_name = request.POST.get('child_name')
            student.sex = request.POST.get('sex')
            student.dob = request.POST.get('dob')
            student.handedness = request.POST.get('handedness')
            student.studying = request.POST.get('studying')
            student.birth_order = request.POST.get('birth_order')
            student.num_siblings = int(request.POST.get('num_siblings', 0))
            student.lrn = request.POST.get('lrn')  # Add LRN field

            # Address info
            student.address = request.POST.get('address')
            student.barangay = request.POST.get('barangay')
            student.municipality = request.POST.get('municipality')
            student.province = request.POST.get('province')
            student.region = request.POST.get('region')

            # Father's info
            student.father_name = request.POST.get('father_name')
            student.father_age = int(request.POST.get('father_age', 0))
            student.father_occupation = request.POST.get('father_occupation')
            student.father_education = request.POST.get('father_education')

            # Mother's info
            student.mother_name = request.POST.get('mother_name')
            student.mother_age = int(request.POST.get('mother_age', 0))
            student.mother_occupation = request.POST.get('mother_occupation')
            student.mother_education = request.POST.get('mother_education')

            # Save the updated student information
            student.save()
            print(f"Updated student record for: {student.child_name}")

            messages.success(request, f'Student information updated successfully for {student.child_name}')
            return redirect('manage_student_session')

        except Exception as e:
            print(f"Error editing student: {str(e)}")
            messages.error(request, f'Error updating student information: {str(e)}')
            return redirect('manage_student_session')

    # If not a POST request, redirect back to the management page
    return redirect('manage_student_session')


def login_view(request):
    if request.method == 'POST':
        # Form field is named username but contains email
        email = request.POST.get('username')
        password = request.POST.get('password')

        print(f"Login attempt with email: {email}")  # Debug log

        # Try to find user by email first - using filter().first() instead of
        # get() to handle multiple users
        user = User.objects.filter(email=email).first()
        if user:
            print(f"Found user with email: {email}")  # Debug log

            # Now authenticate with the username
            auth_user = authenticate(
                request, username=user.username, password=password)
            if auth_user is not None:
                login(request, auth_user)
                print(
                    f"User authenticated successfully. Is staff: {
                        auth_user.is_staff}")  # Debug log

                if auth_user.is_staff:
                    print("Redirecting to teacher dashboard")  # Debug log
                    return redirect('dashboard')
                else:
                    print("Redirecting to parent dashboard")  # Debug log
                    return redirect('dashboard')
            else:
                print(f"Authentication failed - invalid password")  # Debug log
                messages.error(request, 'Invalid email or password')
                return render(
                    request, 'Login.html', {
                        'error': 'Invalid email or password'})
        else:
            print(f"No user found with email: {email}")  # Debug log
            messages.error(request, 'Invalid email or password')
            return render(
                request, 'Login.html', {
                    'error': 'Invalid email or password'})

    return render(request, 'Login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


def pdf_view(request):
    """
    View function for the settings page.
    """
    from .models import PDFFile
    pdf_files = PDFFile.objects.all().order_by('-uploaded_at')
    return render(request, 'PDFFiles.html', {'pdf_files': pdf_files})



def calculate_progress(initial_score, final_score):
    """Helper function to calculate progress percentage between two scores"""
    if initial_score == 0:
        return 0  # Avoid division by zero

    progress = ((final_score - initial_score) / initial_score) * 100
    return max(0, progress)  # Don't show negative progress


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
                student = Student.objects.filter(gmail=user.username).first()
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
                student = Student.objects.filter(gmail=user.username).first()
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
    Uses the EvaluationData and EvaluationDataTeacher models.
    """
    from django.http import JsonResponse
    from django.db.models import Q
    from .models import (
        Student, EvaluationData, EvaluationDataTeacher
    )

    student_name = request.GET.get('student_name', '').strip()

    if not student_name:
        # Try to find student from logged-in user
        username = request.user.username
        email = request.user.email if hasattr(request.user, 'email') else ''

        try:
            # First check gmail fields
            student = Student.objects.filter(
                Q(gmail=username) | Q(gmail=email)).first()

            # Then try parent_email
            if not student:
                student = Student.objects.filter(
                    Q(parent_email=username) | Q(parent_email=email)).first()

            # If we found a student, use their name
            if student:
                student_name = student.child_name.strip()
                print(f"Found student from user: {student_name}")
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No student linked to your account. Please update your profile.'
                }, status=400)
        except Exception as e:
            print(f"Error finding student for user: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'Student name is required and no student was found for your account'
            }, status=400)

    try:
        print(f"Fetching performance data for student: '{student_name}'")

        # Simplified approach: use a case-insensitive search with different whitespace patterns
        # Create a list of possible name patterns to try - include extra
        # whitespace variations
        clean_name = student_name.strip()
        name_patterns = [
            clean_name,               # Trimmed name
            f"{clean_name} ",         # Name with one trailing space
            f" {clean_name}",         # Name with one leading space
            f"{clean_name}  "         # Name with two trailing spaces
        ]

        # Also add variations of the name for broader matching
        name_parts = clean_name.split()
        if len(name_parts) > 1:
            # Try first name only if multi-part name
            name_patterns.append(name_parts[0])
            # Try last name only if multi-part name
            name_patterns.append(name_parts[-1])

        print(f"Trying name patterns: {name_patterns}")

        # Define the evaluation domains we'll be working with
        domains = {
            'GROSS_MOTOR': 'gross_motor',
            'FINE_MOTOR': 'fine_motor',
            'SELF_HELP': 'self_help',
            'COGNITIVE': 'cognitive',
            'EXPRESSIVE': 'expressive',
            'RECEPTIVE': 'receptive',
            'SOCIAL': 'social'
        }

        # Also create domain mappings to handle variations in the database
        domain_mappings = {
            # Standard format
            'GROSS_MOTOR': 'GROSS_MOTOR',
            'FINE_MOTOR': 'FINE_MOTOR',
            'SELF_HELP': 'SELF_HELP',
            'COGNITIVE': 'COGNITIVE',
            'EXPRESSIVE': 'EXPRESSIVE',
            'RECEPTIVE': 'RECEPTIVE',
            'SOCIAL': 'SOCIAL',

            # With _DOMAIN suffix
            'GROSS_MOTOR_DOMAIN': 'GROSS_MOTOR',
            'FINE_MOTOR_DOMAIN': 'FINE_MOTOR',
            'SELF_HELP_DOMAIN': 'SELF_HELP',
            'COGNITIVE_DOMAIN': 'COGNITIVE',
            'EXPRESSIVE_LANGUAGE_DOMAIN': 'EXPRESSIVE',
            'RECEPTIVE_LANGUAGE_DOMAIN': 'RECEPTIVE',
            'SOCIAL_EMOTIONAL_DOMAIN': 'SOCIAL',

            # With hyphens
            'GROSS-MOTOR': 'GROSS_MOTOR',
            'FINE-MOTOR': 'FINE_MOTOR',
            'SELF-HELP': 'SELF_HELP',
            'SELF-HELP_DOMAIN': 'SELF_HELP',
            'COGNITIVE-DOMAIN': 'COGNITIVE',
            'EXPRESSIVE-LANGUAGE': 'EXPRESSIVE',
            'RECEPTIVE-LANGUAGE': 'RECEPTIVE',
            'SOCIAL-EMOTIONAL': 'SOCIAL',
            'SOCIO-EMOTIONAL_DOMAIN': 'SOCIAL'
        }

        # Get teacher evaluations - try all name patterns
        teacher_evaluations = {}
        parent_evaluations = {}

        # Try exact match first
        teacher_evals = EvaluationDataTeacher.objects.filter(
            child_name__iexact=clean_name, evaluator_type='TEACHER')
        parent_evals = EvaluationData.objects.filter(
            child_name__iexact=clean_name, evaluator_type='PARENT')

        # If nothing found with exact match, try broader search using name
        # patterns
        if not teacher_evals.exists() and not parent_evals.exists():
            print(f"No exact matches found, trying partial matches")

            # Try each pattern individually to find matches
            for pattern in name_patterns:
                if pattern == clean_name:  # Skip the exact match we already tried
                    continue

                # Look for this pattern in evaluations
                teacher_matches = EvaluationDataTeacher.objects.filter(
                    child_name__icontains=pattern,
                    evaluator_type='TEACHER'
                )
                parent_matches = EvaluationData.objects.filter(
                    child_name__icontains=pattern,
                    evaluator_type='PARENT'
                )

                # If we found matches, use them
                if teacher_matches.exists() or parent_matches.exists():
                    print(f"Found matches using pattern: '{pattern}'")
                    teacher_evals = teacher_matches
                    parent_evals = parent_matches
                    break

        # Process teacher evaluations
        for eval_type in domains.keys():
            # Need to search for any evaluation_type that maps to this domain
            matching_evals = []
            for db_type, mapped_type in domain_mappings.items():
                if mapped_type == eval_type:
                    db_matches = teacher_evals.filter(evaluation_type=db_type)
                    matching_evals.extend(list(db_matches))

            if matching_evals:
                # Use the first match found
                teacher_evaluations[eval_type] = matching_evals[0]
                print(
                    f"Found teacher evaluation for {eval_type}: {
                        matching_evals[0].evaluation_type}")

        # Process parent evaluations
        for eval_type in domains.keys():
            # Need to search for any evaluation_type that maps to this domain
            matching_evals = []
            for db_type, mapped_type in domain_mappings.items():
                if mapped_type == eval_type:
                    db_matches = parent_evals.filter(evaluation_type=db_type)
                    matching_evals.extend(list(db_matches))

            if matching_evals:
                # Use the first match found
                parent_evaluations[eval_type] = matching_evals[0]
                print(
                    f"Found parent evaluation for {eval_type}: {
                        matching_evals[0].evaluation_type}")

        # Debug output
        print(
            f"Teacher evaluations found: {
                ', '.join(
                    [
                        k for k,
                        v in teacher_evaluations.items() if v])}")
        print(
            f"Parent evaluations found: {', '.join([k for k, v in parent_evaluations.items() if v])}")

        # More detailed debug output to help with troubleshooting
        print("Teacher evaluation details:")
        for k, v in teacher_evaluations.items():
            if v:
                print(
                    f"  {k}: {
                        v.evaluation_type}, scores: {
                        v.first_eval_score}/{
                        v.second_eval_score}/{
                        v.third_eval_score}")

        print("Parent evaluation details:")
        for k, v in parent_evaluations.items():
            if v:
                print(
                    f"  {k}: {
                        v.evaluation_type}, scores: {
                        v.first_eval_score}/{
                        v.second_eval_score}/{
                        v.third_eval_score}")

        # If no evaluations were found at all, return a warning response
        if not teacher_evaluations and not parent_evaluations:
            print(f"No evaluations found for student: {student_name}")
            return JsonResponse({
                'status': 'warning',
                'message': f"No evaluation data found for student: {student_name}",
                'student_name': student_name,
                'table_data': {},
                'chart_data': {'labels': [], 'datasets': []},
                'totals': {}
            })

        # Create data structure for table display
        table_data = {}

        # Initialize table data with all domains
        for eval_type, domain_key in domains.items():
            teacher_eval = teacher_evaluations.get(eval_type)
            parent_eval = parent_evaluations.get(eval_type)

            table_data[domain_key] = {
                'teacher_eval1': teacher_eval.first_eval_score if teacher_eval else 0,
                'teacher_eval2': teacher_eval.second_eval_score if teacher_eval else 0,
                'teacher_eval3': teacher_eval.third_eval_score if teacher_eval else 0,
                'parent_eval1': parent_eval.first_eval_score if parent_eval else 0,
                'parent_eval2': parent_eval.second_eval_score if parent_eval else 0,
                'parent_eval3': parent_eval.third_eval_score if parent_eval else 0,
            }

        # Create data for chart visualization
        chart_data = {
            'labels': ['1st Evaluation', '2nd Evaluation', '3rd Evaluation'],
            'datasets': []
        }

        # Domain colors for charts
        domain_colors = {
            'gross_motor': {'border': 'rgb(255, 99, 132)', 'background': 'rgba(255, 99, 132, 0.2)'},
            'fine_motor': {'border': 'rgb(54, 162, 235)', 'background': 'rgba(54, 162, 235, 0.2)'},
            'self_help': {'border': 'rgb(75, 192, 192)', 'background': 'rgba(75, 192, 192, 0.2)'},
            'receptive': {'border': 'rgb(153, 102, 255)', 'background': 'rgba(153, 102, 255, 0.2)'},
            'expressive': {'border': 'rgb(255, 159, 64)', 'background': 'rgba(255, 159, 64, 0.2)'},
            'cognitive': {'border': 'rgb(255, 205, 86)', 'background': 'rgba(255, 205, 86, 0.2)'},
            'social': {'border': 'rgb(201, 203, 207)', 'background': 'rgba(201, 203, 207, 0.2)'}
        }

        # Domain display names for charts
        domain_names = {
            'gross_motor': 'Gross Motor',
            'fine_motor': 'Fine Motor',
            'self_help': 'Self Help',
            'receptive': 'Receptive Language',
            'expressive': 'Expressive Language',
            'cognitive': 'Cognitive',
            'social': 'Social-Emotional'
        }

        # Add datasets for each domain from teacher evaluations
        for eval_type, domain_key in domains.items():
            teacher_eval = teacher_evaluations.get(eval_type)
            parent_eval = parent_evaluations.get(eval_type)

            # Only include domains that have at least some data (teacher or
            # parent)
            if teacher_eval or parent_eval:
                chart_data['datasets'].append({
                    'label': domain_names[domain_key],
                    'data': [
                        teacher_eval.first_eval_score if teacher_eval else 0,
                        teacher_eval.second_eval_score if teacher_eval else 0,
                        teacher_eval.third_eval_score if teacher_eval else 0
                    ],
                    'borderColor': domain_colors[domain_key]['border'],
                    'backgroundColor': domain_colors[domain_key]['background']
                })

        # Calculate total scores for each domain
        totals = {}
        for domain_key in domains.values():
            domain_data = table_data[domain_key]
            totals[domain_key] = sum(
                [value for key, value in domain_data.items() if isinstance(value, int)]
            )

        response_data = {
            'status': 'success',
            'student_name': student_name,
            'table_data': table_data,
            'chart_data': chart_data,
            'totals': totals
        }

        print(f"Sending response with data for student: {student_name}")
        return JsonResponse(response_data)

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

        messages.success(
            request, f'{
                len(pdf_files)} PDF file(s) uploaded successfully.')
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

    # Get current school year and all school years
    current_school_year = SchoolYear.get_current_school_year()
    school_years = SchoolYear.get_all_school_years()

    # Check if user is a student
    student = Student.objects.filter(gmail=user.username).first()

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
        'current_school_year': current_school_year.year if current_school_year else None,
        'school_years': school_years,
        'all_students': all_students,
        'success_message': success_message,
        'error_message': error_message,
        'is_staff': user.is_staff,
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
                student = Student.objects.filter(gmail=user.username).first()
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
                student = Student.objects.filter(gmail=user.username).first()
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
            return render(
                request, 'forgot_password.html', {
                    'error': 'Please enter your username'})

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
        messages.success(
            request,
            'Password has been reset successfully. Please log in with your new password.')
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
        messages.error(
            request,
            "You don't have permission to create announcements.")
        return redirect('dashboard')

    # Get all announcements for display
    announcements = Announcement.objects.all().order_by(
        '-created_at')[:10]  # Show 10 most recent

    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')

        # Validate form data
        if not title or not content:
            messages.error(
                request, "Please fill in both title and content fields.")
            return render(
                request, 'create_announcement.html', {
                    'announcements': announcements})

        # Create new announcement
        announcement = Announcement(
            title=title,
            content=content,
            created_by=request.user
        )
        announcement.save()

        messages.success(request, "Announcement created successfully!")
        return redirect('dashboard')

    # GET request - display the form
    return render(
        request, 'create_announcement.html', {
            'announcements': announcements})


@login_required
def view_announcements(request):
    """
    View function to display all active announcements.
    """
    announcements = Announcement.objects.filter(
        is_active=True).order_by('-created_at')
    return render(request, 'view_announcements.html',
                  {'announcements': announcements})


@login_required
def delete_announcement(request, announcement_id):
    """
    View function to delete an announcement.
    Only staff members can delete announcements.
    """
    if not request.user.is_staff:
        messages.error(
            request,
            "You don't have permission to delete announcements.")
        return redirect('dashboard')

    announcement = get_object_or_404(Announcement, id=announcement_id)
    announcement.delete()

    messages.success(request, "Announcement deleted successfully!")
    return redirect('dashboard')


@login_required
def teacher_evaluation_pdfs(request):
    """
    View for displaying teacher's evaluation data for the logged-in user's associated student.
    """
    import json  # Import json at the function level to ensure it's available

    # Get the logged-in user's username
    username = request.user.username

    # Get student based on the username
    student = Student.objects.filter(gmail=username).first()

    if not student:
        # Handle case where student is not found
        context = {
            'error_message': 'No student record found for your account.'
        }
        return render(request, 'teacher_evaluation_pdfs.html', context)

    # Get the student's name
    student_name = student.child_name

    # Fetch all evaluations for this student from EvaluationDataTeacher model
    all_evaluations = EvaluationDataTeacher.objects.filter(
        child_name=student_name).order_by('-created_at')

    # Debug print
    print(
        f"Found {
            all_evaluations.count()} evaluations for student: {student_name}")

    # Process evaluations by type
    evaluations = {
        'gross_motor': {
            'label': 'Gross Motor',
            'reports': []
        },
        'fine_motor': {
            'label': 'Fine Motor',
            'reports': []
        },
        'self_help': {
            'label': 'Self Help',
            'reports': []
        },
        'cognitive': {
            'label': 'Cognitive',
            'reports': []
        },
        'expressive': {
            'label': 'Expressive Language',
            'reports': []
        },
        'receptive': {
            'label': 'Receptive Language',
            'reports': []
        },
        'social': {
            'label': 'Social-Emotional',
            'reports': []
        }
    }

    # Map evaluation types from database to template keys
    eval_type_mapping = {
        'GROSS_MOTOR': 'gross_motor',
        'FINE_MOTOR': 'fine_motor',
        'SELF_HELP': 'self_help',
        'COGNITIVE': 'cognitive',
        'EXPRESSIVE': 'expressive',
        'RECEPTIVE': 'receptive',
        'SOCIAL': 'social'
    }

    # Populate evaluations dictionary with data from the database
    for evaluation in all_evaluations:
        template_key = eval_type_mapping.get(evaluation.evaluation_type)
        if template_key and template_key in evaluations:
            # Handle JSON serialization of data
            try:
                # First, check if evaluation.data is already a string
                if isinstance(evaluation.data, str):
                    print(
                        f"Data is already a string for evaluation ID: {
                            evaluation.id}")
                    # Try to parse it to ensure it's valid JSON
                    try:
                        parsed_data = json.loads(evaluation.data)
                        data_json = evaluation.data  # Use the original string if valid
                    except json.JSONDecodeError:
                        print(
                            f"Invalid JSON string in data field for evaluation ID: {
                                evaluation.id}")
                        # Fallback to an empty JSON structure
                        data_json = json.dumps({
                            "rows": [
                                {"name": "Data could not be parsed", "eval1": False, "eval2": False, "eval3": False}
                            ],
                            "notes": "Error: The stored data is not in a valid format."
                        })
                else:
                    # It's a Python object, serialize it
                    print(
                        f"Serializing data for evaluation ID: {
                            evaluation.id}")
                    data_json = json.dumps(evaluation.data)
            except Exception as e:
                print(
                    f"Error handling data for evaluation ID {
                        evaluation.id}: {
                        str(e)}")
                # Provide a fallback JSON structure
                data_json = json.dumps({
                    "rows": [
                        {"name": "Data could not be loaded", "eval1": False, "eval2": False, "eval3": False}
                    ],
                    "notes": f"Error loading data: {str(e)}"
                })

            # Add the report entry
            evaluations[template_key]['reports'].append({
                'first_eval_score': evaluation.first_eval_score,
                'second_eval_score': evaluation.second_eval_score,
                'third_eval_score': evaluation.third_eval_score,
                'created_at': evaluation.created_at,
                'data': data_json
            })
            print(
                f"Added evaluation type {
                    evaluation.evaluation_type} to {template_key} reports")

    # Remove empty evaluation types
    evaluations = {k: v for k, v in evaluations.items() if v['reports']}
    print(f"Final evaluations categories: {', '.join(evaluations.keys())}")

    context = {
        'evaluations': evaluations,
        'student_name': student_name
    }

    return render(request, 'teacher_evaluation_pdfs.html', context)


@login_required
def student_full_report(request):
    """
    View function to render the full student performance report.
    This view requires a student_name parameter in the query string.
    If no student_name is provided, it will attempt to use the logged-in user's student.
    The actual data is loaded via AJAX from get_student_performance_data.
    """
    print("Loading student_full_report view")
    student_name = request.GET.get('student_name', '').strip()

    # If no student name provided, try to get it from the logged-in user
    if not student_name:
        # Get the username and email of the logged-in user
        username = request.user.username
        email = request.user.email
        print(
            f"No student name provided. Getting student for user: {username}")

        # Try to find a student associated with this user
        try:
            from .models import Student

            # Try multiple ways to find a student
            student = None

            # First check if there's a student with gmail matching username
            student = Student.objects.filter(gmail=username).first()

            # If not found, try with email
            if not student and email:
                student = Student.objects.filter(gmail=email).first()

            # If still not found, try parent_email fields
            if not student:
                student = Student.objects.filter(parent_email=username).first()

            if not student and email:
                student = Student.objects.filter(parent_email=email).first()

            # If still not found, check if username matches child_name
            if not student:
                # Try case-insensitive search for child_name
                student = Student.objects.filter(
                    child_name__icontains=username).first()

            # Check if we found a student
            if student:
                student_name = student.child_name.strip()
                print(f"Found student: {student_name}")
            else:
                # If still not found and the user is staff, let's get the first
                # student
                if request.user.is_staff:
                    student = Student.objects.order_by('child_name').first()
                    if student:
                        student_name = student.child_name.strip()
                        print(
                            f"Staff user - using first student: {student_name}")
                    else:
                        print("No students found in the database")
                else:
                    print(f"No student found for user {username}")
        except Exception as e:
            print(f"Error getting student for user: {str(e)}")

    # Even if no name is provided or found, we'll still render the template
    context = {
        'title': f"{student_name}'s Full Report" if student_name else "Student Full Report",
        'student_name': student_name  # Pass the student name to the template
    }

    print(
        f"Rendering studentfullreport.html with student_name: '{student_name}'")
    return render(request, 'studentfullreport.html', context)


@login_required
def load_evaluation_data(request, table_id):
    """
    View to load existing evaluation data for a specific table and student.
    """
    try:
        # Get parameters from request
        student_name = request.GET.get('student')
        evaluator_type = request.GET.get('evaluator_type', 'PARENT')

        # Get the table
        table = get_object_or_404(EditableEvaluationTable, id=table_id)

        # If we're loading for a parent, get student from user email
        if evaluator_type == 'PARENT':
            # Get student associated with logged-in user's email
            student = Student.objects.filter(gmail=request.user.email).first()
            if not student:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No student found for this account'
                })
            student_name = student.child_name

        # If no student name provided and we're not loading for a parent,
        # return error
        if not student_name and evaluator_type != 'PARENT':
            return JsonResponse({
                'status': 'error',
                'message': 'No student name provided'
            })

        # Get existing evaluation data if any
        evaluation_type = table.name.upper().replace(' ', '_')

        # Use the appropriate model based on evaluator type
        if evaluator_type == 'TEACHER':
            existing_evaluation = EvaluationDataTeacher.objects.filter(
                child_name=student_name,
                evaluation_type=evaluation_type,
                evaluator_type='TEACHER'
            ).first()
        else:
            existing_evaluation = EvaluationData.objects.filter(
                child_name=student_name,
                evaluation_type=evaluation_type,
                evaluator_type='PARENT'
            ).first()

        if existing_evaluation:
            return JsonResponse({
                'status': 'success',
                'data': existing_evaluation.data,
                'first_eval_score': existing_evaluation.first_eval_score,
                'second_eval_score': existing_evaluation.second_eval_score,
                'third_eval_score': existing_evaluation.third_eval_score,
            })
        else:
            return JsonResponse({
                'status': 'success',
                'data': None
            })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

# Add the submit_expressive_evaluation function


def submit_expressive_evaluation(request):
    if request.method == 'POST':
        # Import needed models
        from .models import ExpressiveEvaluation, EvaluationDataTeacher
        import json

        student_name = request.POST.get('student_name')
        eval1_score = int(request.POST.get('eval1_score', 0) or 0)
        eval2_score = int(request.POST.get('eval2_score', 0) or 0)
        eval3_score = int(request.POST.get('eval3_score', 0) or 0)

        # Create the expressive evaluation record
        try:
            ExpressiveEvaluation.objects.create(
                student_name=student_name,
                eval1_score=eval1_score,
                eval2_score=eval2_score,
                eval3_score=eval3_score
            )
            print("ExpressiveEvaluation record created successfully")
        except Exception as e:
            print(f"Error creating ExpressiveEvaluation record: {str(e)}")
            import traceback
            traceback.print_exc()
            messages.error(
                request, 'Error saving evaluation data. Please try again.')
            return redirect('dashboard')

        # Prepare form data for EvaluationDataTeacher
        try:
            # Get checkbox states from the form
            checkboxes = {}
            rows = []

            for i in range(1, 3):  # 2 evaluation items for expressive
                # Get checkbox states from the POST data
                eval1 = request.POST.get(f'checkbox_{i}_eval1') == 'on'
                eval2 = request.POST.get(f'checkbox_{i}_eval2') == 'on'
                eval3 = request.POST.get(f'checkbox_{i}_eval3') == 'on'

                # Define the items
                item_names = {
                    1: "Uses 5 to 20 recognizable words",
                    2: "Names object in pictures"
                }

                # Add to rows
                rows.append({
                    "name": item_names.get(i, f"Item {i}"),
                    "eval1": eval1,
                    "eval2": eval2,
                    "eval3": eval3
                })

            # Create form data structure
            form_data = {
                "rows": rows,
                "notes": "Evaluation completed on " +
                datetime.now().strftime('%B %d, %Y')}

            # Save to EvaluationDataTeacher
            evaluation, created = EvaluationDataTeacher.objects.update_or_create(
                child_name=student_name,
                evaluation_type='EXPRESSIVE',
                evaluator_type='TEACHER',
                defaults={
                    'first_eval_score': eval1_score,
                    'second_eval_score': eval2_score,
                    'third_eval_score': eval3_score,
                    'data': form_data
                }
            )

            messages.success(
                request, 'Expressive language evaluation saved successfully!')

        except Exception as e:
            print(f"Error saving evaluation data: {str(e)}")
            import traceback
            traceback.print_exc()
            messages.warning(
                request, f'Partial data saved. Some information may be missing.')

        return redirect('dashboard')


@login_required
def get_evaluation_tables(request):
    """
    View to get all available evaluation tables.
    Returns a JSON list of tables with their IDs and names.
    The tables are filtered based on whether the user is staff (teacher) or not (parent).
    """
    try:
        is_staff = request.user.is_staff
        evaluator_type = 'TEACHER' if is_staff else 'PARENT'

        # Get tables based on evaluator type
        tables = EditableEvaluationTable.objects.filter(
            evaluator_type__in=[evaluator_type, 'BOTH']).order_by('name')

        table_list = [
            {
                'id': table.id,
                'name': table.name,
                'evaluator_type': table.evaluator_type
            }
            for table in tables
        ]

        return JsonResponse({
            'status': 'success',
            'tables': table_list
        })
    except Exception as e:
        print(f"Error in get_evaluation_tables: {str(e)}")  # Add logging
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred while fetching evaluation tables'
        }, status=500)


@login_required
def teacher_evaluation_tables(request):
    """
    View to display the teacher evaluation tables interface.
    Teachers can select students and tables to evaluate.
    """
    # Only staff members (teachers) can access this view
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access teacher evaluations.")
        return redirect('dashboard')

    # Get all students for the dropdown
    students = Student.objects.all().order_by('child_name')

    # Get all evaluation tables
    tables = EditableEvaluationTable.objects.filter(evaluator_type__in=['TEACHER', 'BOTH']).order_by('name')

    context = {
        'students': students,
        'tables': tables
    }

    return render(request, 'teacher_evaluation_tables.html', context)


@login_required
def parent_evaluation_tables(request):
    """
    View to display the parent evaluation tables interface.
    Parents can only evaluate their own children.
    """
    # Get the parent's child
    user_email = request.user.email
    student = Student.objects.filter(gmail=user_email).first()

    if not student:
        messages.error(request, "No student found for your account.")
        return redirect('dashboard')

    # Get evaluation tables that are accessible to parents
    tables = EditableEvaluationTable.objects.filter(
        evaluator_type__in=['PARENT', 'BOTH']
    ).order_by('name')

    context = {
        'student': student,
        'student_name': student.child_name,  # Add student name for the hidden input
        'tables': tables
    }

    return render(request, 'parent_evaluation_tables.html', context)


@login_required
def view_evaluation_table(request, table_id):
    """
    API view to get evaluation table data.
    Returns JSON data containing the table structure and metadata.
    """
    try:
        # Get the table
        table = get_object_or_404(EditableEvaluationTable, id=table_id)

        # Determine if this is a teacher or parent user
        is_staff = request.user.is_staff
        evaluator_type = 'TEACHER' if is_staff else 'PARENT'

        # Check if user has permission to view this table
        if table.evaluator_type not in [evaluator_type, 'BOTH']:
            return JsonResponse({
                'status': 'error',
                'message': "You don't have permission to view this evaluation table."
            }, status=403)

        # Return the table data
        return JsonResponse({
            'status': 'success',
            'table': {
                'id': table.id,
                'name': table.name,
                'evaluator_type': table.evaluator_type,
                'data': table.data
            }
        })
    except Exception as e:
        print(f"Error in view_evaluation_table: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred while fetching the evaluation table'
        }, status=500)


@login_required
def get_all_students(request):
    """
    API view to get a list of all students.
    Returns a JSON list of students with their IDs and names.
    """
    try:
        # Only staff members can access this API
        if not request.user.is_staff:
            return JsonResponse({
                'status': 'error',
                'message': "You don't have permission to access this data."
            }, status=403)

        students = Student.objects.all().order_by('child_name')

        student_list = [
            {'id': student.id, 'name': student.child_name}
            for student in students
        ]

        return JsonResponse({
            'status': 'success',
            'students': student_list
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def save_evaluation(request, table_id):
    """
    API view to save evaluation data for a specific table.
    The data is saved to either EvaluationData or EvaluationDataTeacher
    based on the evaluator_type.
    """
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Only POST method is allowed'
        }, status=405)

    try:
        # Parse the JSON data from the request
        data = json.loads(request.body)
        evaluation_data = data.get('data', {})

        if not evaluation_data:
            return JsonResponse({
                'status': 'error',
                'message': 'No evaluation data provided'
            }, status=400)

        # Get required parameters
        student_name = evaluation_data.get('child_name')
        evaluator_type = evaluation_data.get('evaluator_type', 'PARENT')
        first_eval_score = evaluation_data.get('first_eval_score', 0)
        second_eval_score = evaluation_data.get('second_eval_score', 0)
        third_eval_score = evaluation_data.get('third_eval_score', 0)
        table_data = evaluation_data.get('data', {})

        # Get the table
        table = get_object_or_404(EditableEvaluationTable, id=table_id)
        evaluation_type = evaluation_data.get('evaluation_type') or table.name.upper().replace(' ', '_')

        # Check if user has permission to save data
        is_staff = request.user.is_staff
        if evaluator_type == 'TEACHER' and not is_staff:
            return JsonResponse({
                'status': 'error',
                'message': "You don't have permission to save teacher evaluations."
            }, status=403)

        # If parent, make sure they're saving for their own child
        if not is_staff:
            user_email = request.user.email
            parent_student = Student.objects.filter(gmail=user_email).first()

            if not parent_student or parent_student.child_name != student_name:
                return JsonResponse({
                    'status': 'error',
                    'message': "You can only save evaluations for your own child."
                }, status=403)

        print(f"Saving evaluation for student: {student_name}, type: {evaluation_type}, evaluator: {evaluator_type}")

        # Find existing evaluation
        if evaluator_type == 'TEACHER':
            existing_evaluation = EvaluationDataTeacher.objects.filter(
                child_name=student_name,
                evaluation_type=evaluation_type,
                evaluator_type=evaluator_type
            ).first()
        else:
            existing_evaluation = EvaluationData.objects.filter(
                child_name=student_name,
                evaluation_type=evaluation_type,
                evaluator_type=evaluator_type
            ).first()

        # Update or create the evaluation
        if existing_evaluation:
            print(f"Updating existing evaluation (ID: {existing_evaluation.id})")
            # Update existing record
            existing_evaluation.first_eval_score = first_eval_score
            existing_evaluation.second_eval_score = second_eval_score
            existing_evaluation.third_eval_score = third_eval_score
            existing_evaluation.data = table_data
            existing_evaluation.save()
            created = False
        else:
            print("Creating new evaluation record")
            # Create new record
            if evaluator_type == 'TEACHER':
                EvaluationDataTeacher.objects.create(
                    child_name=student_name,
                    evaluation_type=evaluation_type,
                    evaluator_type=evaluator_type,
                    first_eval_score=first_eval_score,
                    second_eval_score=second_eval_score,
                    third_eval_score=third_eval_score,
                    data=table_data
                )
            else:
                EvaluationData.objects.create(
                    child_name=student_name,
                    evaluation_type=evaluation_type,
                    evaluator_type=evaluator_type,
                    first_eval_score=first_eval_score,
                    second_eval_score=second_eval_score,
                    third_eval_score=third_eval_score,
                    data=table_data
                )
            created = True

        return JsonResponse({
            'status': 'success',
            'message': 'Evaluation data saved successfully',
            'created': created
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)

    except Exception as e:
        print(f"Error in save_evaluation: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'An error occurred while saving the evaluation: {str(e)}'
        }, status=500)


@login_required
def readonly_evaluation_forms(request):
    """
    View to display evaluation forms in read-only mode.
    This is useful for parents to view evaluations without being able to edit them.
    """
    student_name = request.GET.get('student_name', '')
    evaluation_type = request.GET.get('evaluation_type', '')

    # Get all evaluation data for this student
    evaluations = {
        'teacher': EvaluationDataTeacher.objects.all(),
        'parent': EvaluationData.objects.all()
    }

    if student_name:
        evaluations['teacher'] = evaluations['teacher'].filter(child_name__icontains=student_name)
        evaluations['parent'] = evaluations['parent'].filter(child_name__icontains=student_name)

    if evaluation_type:
        evaluations['teacher'] = evaluations['teacher'].filter(evaluation_type=evaluation_type)
        evaluations['parent'] = evaluations['parent'].filter(evaluation_type=evaluation_type)

    # Order by most recent
    evaluations['teacher'] = evaluations['teacher'].order_by('-created_at')
    evaluations['parent'] = evaluations['parent'].order_by('-created_at')

    context = {
        'evaluations': evaluations,
        'student_name': student_name,
        'evaluation_type': evaluation_type,
        'evaluation_types': [
            ('GROSS_MOTOR', 'Gross Motor'),
            ('FINE_MOTOR', 'Fine Motor'),
            ('SELF_HELP', 'Self Help'),
            ('COGNITIVE', 'Cognitive'),
            ('EXPRESSIVE', 'Expressive Language'),
            ('RECEPTIVE', 'Receptive Language'),
            ('SOCIAL', 'Social-Emotional')
        ]
    }

    return render(request, 'readonly_evaluation_forms.html', context)


@login_required
def evaluation_management(request):
    """
    View to manage evaluation forms and tables.
    Only staff members can access this view.
    """
    # Only staff members can access this view
    if not request.user.is_staff:
        messages.error(
            request,
            "You don't have permission to access evaluation management.")
        return redirect('dashboard')

    # Get all evaluation tables
    tables = EditableEvaluationTable.objects.all().order_by('name')

    context = {
        'tables': tables
    }

    return render(request, 'evaluation_checklists/evaluation_management.html', context)


@login_required
def save_evaluation_management(request):
    """
    API view to save evaluation management settings.
    """
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Only POST method is allowed'
        }, status=405)

    try:
        # Only staff members can access this API
        if not request.user.is_staff:
            return JsonResponse({
                'status': 'error',
                'message': "You don't have permission to update evaluation forms."
            }, status=403)

        # Parse the JSON data from the request
            data = json.loads(request.body)

        # Get the tables to update
        tables = data.get('tables', [])

        # Update each table
        for table_data in tables:
            table_id = table_data.get('id')
            name = table_data.get('name')
            description = table_data.get('description', '')
            evaluator_type = table_data.get('evaluator_type', 'BOTH')

            if table_id:
                # Update existing table
                table = get_object_or_404(EditableEvaluationTable, id=table_id)
                table.name = name
                table.description = description
                table.evaluator_type = evaluator_type
                table.save()
            else:
                # Create new table
                EditableEvaluationTable.objects.create(
                    name=name,
                    description=description,
                    evaluator_type=evaluator_type
                )

            return JsonResponse({
                'status': 'success',
                'message': 'Evaluation management settings saved successfully'
            })

    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def get_saved_evaluation_forms(request):
    """
    API view to get all saved evaluation forms.
    Returns a JSON list of evaluation forms.
    """
    try:
        # Only staff members can access this API
        if not request.user.is_staff:
            return JsonResponse({
                'status': 'error',
                'message': "You don't have permission to access this data."
            }, status=403)

        # Get all evaluation forms from EditableEvaluationTable
        forms = EditableEvaluationTable.objects.all().order_by('-created_at')

        # Prepare the forms data
        forms_data = [
            {
                'id': form.id,
                'name': form.name,
                'evaluator_type': form.evaluator_type,
                'created_at': form.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': form.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            for form in forms
        ]

        return JsonResponse({
            'status': 'success',
            'forms': forms_data
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def get_evaluation_form_data(request, form_id):
    """
    API view to get the data for a specific evaluation form.
    Handles both form templates (EditableEvaluationTable) and evaluation data (EvaluationDataTeacher).
    """
    try:
        # Only staff members can access this API
        if not request.user.is_staff:
            return JsonResponse({
                'status': 'error',
                'message': "You don't have permission to access this data."
            }, status=403)

        # Check if we're loading a template or evaluation data
        source = request.GET.get('source', 'template')

        if source == 'evaluation':
            # Try to get evaluation data
            try:
                form = EvaluationDataTeacher.objects.get(id=form_id)
                form_data = {
                    'id': form.id,
                    'child_name': form.child_name,
                    'evaluation_type': form.evaluation_type,
                    'first_eval_score': form.first_eval_score,
                    'second_eval_score': form.second_eval_score,
                    'third_eval_score': form.third_eval_score,
                    'created_at': form.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'evaluator_type': form.evaluator_type,
                    'data': form.data
                }
            except EvaluationDataTeacher.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Evaluation data not found'
                }, status=404)
        else:
            # Get the form template
            try:
                form = EditableEvaluationTable.objects.get(id=form_id)
                form_data = {
                    'id': form.id,
                    'name': form.name,
                    'evaluator_type': form.evaluator_type,
                    'created_at': form.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': form.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'data': form.data
                }
            except EditableEvaluationTable.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Form template not found'
                }, status=404)

        return JsonResponse({
            'status': 'success',
            'form': form_data
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def update_evaluation_form(request, form_id):
    """
    View to update or delete an existing evaluation form.
    Handles both form templates (EditableEvaluationTable) and evaluation data (EvaluationDataTeacher).
    """
    try:
        # Only staff members can access this API
        if not request.user.is_staff:
            return JsonResponse({
                'status': 'error',
                'message': "You don't have permission to modify evaluation forms."
            }, status=403)

        # Check if we're updating a template or evaluation data
        source = request.GET.get('source', 'template')

        if source == 'evaluation':
            # Handle evaluation data
            form = get_object_or_404(EvaluationDataTeacher, id=form_id)

            if request.method == 'DELETE':
                form.delete()
                return JsonResponse({
                    'status': 'success',
                    'message': 'Evaluation data deleted successfully'
                })
            elif request.method == 'POST':
                data = json.loads(request.body)
                
                # Update evaluation data fields
                if 'child_name' in data:
                    form.child_name = data['child_name']
                if 'evaluation_type' in data:
                    form.evaluation_type = data['evaluation_type']
                if 'first_eval_score' in data:
                    form.first_eval_score = data['first_eval_score']
                if 'second_eval_score' in data:
                    form.second_eval_score = data['second_eval_score']
                if 'third_eval_score' in data:
                    form.third_eval_score = data['third_eval_score']
                if 'data' in data:
                    form.data = data['data']
                
                form.save()
        else:
            # Handle form template
            form = get_object_or_404(EditableEvaluationTable, id=form_id)

            if request.method == 'DELETE':
                form.delete()
                return JsonResponse({
                    'status': 'success',
                    'message': 'Form template deleted successfully'
                })
            elif request.method == 'POST':
                data = json.loads(request.body)
                
                # Update template fields
                if 'name' in data:
                    form.name = data['name']
                if 'evaluator_type' in data:
                    form.evaluator_type = data['evaluator_type']
                if 'table' in data:
                    form.data = data['table']
                
                form.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Form updated successfully'
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def get_recent_announcements(request):
    """
    API view to get recent announcements.
    Returns a JSON list of recent active announcements.
    """
    try:
        # Get recent active announcements
        announcements = Announcement.objects.filter(
            is_active=True).order_by('-created_at')[:5]

        announcement_list = [
            {
                'id': announcement.id,
                'title': announcement.title,
                'content': announcement.content,
                'created_at': timesince(announcement.created_at),
                'created_by': announcement.created_by.username if announcement.created_by else 'Anonymous'
            }
            for announcement in announcements
        ]

        return JsonResponse(announcement_list, safe=False)
    except Exception as e:
        return JsonResponse([], safe=False)


@login_required
def get_events(request):
    """
    API view to get calendar events.
    Returns a JSON list of events.
    """
    try:
        # Get all events
        events = Event.objects.all().order_by('start_date')

        event_list = [
            {
                'id': event.id,
                'title': event.title,
                'description': event.description,
                'start': event.start_date.isoformat(),
                'end': event.end_date.isoformat() if event.end_date else None,
                'color': event.color,
                'created_by': event.created_by.username if event.created_by else 'Anonymous'
            }
            for event in events
        ]

        return JsonResponse(event_list, safe=False)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def add_event(request):
    """
    API view to add a new calendar event.
    Handles both form submissions and JSON API requests.
    """
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Only POST method is allowed'
        }, status=405)

    try:
        # Check if the request is a JSON request or a form submission
        if request.content_type and 'application/json' in request.content_type:
            # Parse JSON data
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
        else:
            # Handle form data
            data = {
                'title': request.POST.get('title'),
                'description': request.POST.get('description', ''),
                'start_date': request.POST.get('start_date'),
                'end_date': request.POST.get('end_date'),
                'color': request.POST.get('color', '#2d6a4f')  # Default color if not provided
            }

        # Get required parameters
        title = data.get('title')
        description = data.get('description', '')
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        color = data.get('color', '#2d6a4f')  # Default color if not provided

        # Validate required fields
        if not title or not start_date_str:
            if request.content_type and 'application/json' in request.content_type:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Title and start date are required'
                }, status=400)
            messages.error(request, 'Title and start date are required')
            return redirect('dashboard')

        # Parse dates
        from datetime import datetime
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(
                end_date_str, '%Y-%m-%d').date() if end_date_str else None
        except ValueError:
            if request.content_type and 'application/json' in request.content_type:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid date format. Use YYYY-MM-DD.'
                }, status=400)
            messages.error(request, 'Invalid date format. Use YYYY-MM-DD.')
            return redirect('dashboard')

        # Create the event
        event = Event.objects.create(
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date,
            color=color,
            created_by=request.user
        )

        # Respond based on request type
        if request.content_type and 'application/json' in request.content_type:
            return JsonResponse({
                'status': 'success',
                'message': 'Event added successfully',
                'event': {
                    'id': event.id,
                    'title': event.title,
                    'description': event.description,
                    'start_date': event.start_date.strftime('%Y-%m-%d'),
                    'end_date': event.end_date.strftime('%Y-%m-%d') if event.end_date else None,
                    'color': event.color
                }
            })
        else:
            messages.success(request, 'Event added successfully')
            return redirect('dashboard')

    except Exception as e:
        if request.content_type and 'application/json' in request.content_type:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
        else:
            messages.error(request, f'Error adding event: {str(e)}')
            return redirect('dashboard')


@login_required
def delete_event(request, event_id):
    """
    API view to delete a calendar event.
    """
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Only POST method is allowed'
        }, status=405)

    try:
        # Get the event
        event = get_object_or_404(Event, id=event_id)

        # Check if user has permission to delete the event
        if event.created_by != request.user and not request.user.is_staff:
            return JsonResponse({
            'status': 'error',
            'message': "You don't have permission to delete this event."
        }, status=403)

        # Delete the event
        event.delete()

        return JsonResponse({
            'status': 'success',
            'message': 'Event deleted successfully'
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@login_required
def view_teacher_evaluations(request):
    """
    View function to display teacher evaluations in read-only mode for parents.
    """
    try:
        # Get the logged-in user's email
        user_email = request.user.email

        # Get the student associated with this parent
        student = Student.objects.filter(gmail=user_email).first()

        if not student:
            messages.error(request, "No student profile found for your account.")
            return redirect('dashboard')

        # Get all teacher evaluations for this student
        evaluations = EvaluationDataTeacher.objects.filter(
            child_name=student.child_name,
            evaluator_type='TEACHER'
        ).order_by('-created_at')

        # Debug print to check what evaluations are being fetched
        print(f"\nFetching evaluations for student: {student.child_name}")
        print(f"Total evaluations found: {evaluations.count()}")

        # Get all evaluation forms
        evaluation_forms = EditableEvaluationTable.objects.filter(
            evaluator_type__in=['TEACHER', 'BOTH']
        )
        print(f"Found {evaluation_forms.count()} evaluation forms")

        # Create a mapping of evaluation types to their form data
        form_data_mapping = {}
        for form in evaluation_forms:
            eval_type = form.name.upper().replace(' ', '_')
            form_data_mapping[eval_type] = form.data
            print(f"Form data for {eval_type}: {form.data}")

        # Group evaluations by type with proper mapping
        evaluation_type_mapping = {
            'GROSS_MOTOR': 'Gross Motor',
            'GROSS_MOTOR_DOMAIN': 'Gross Motor',
            'FINE_MOTOR': 'Fine Motor',
            'FINE_MOTOR_DOMAIN': 'Fine Motor',
            'SELF_HELP': 'Self Help',
            'SELF_HELP_DOMAIN': 'Self Help',
            'COGNITIVE': 'Cognitive',
            'COGNITIVE_DOMAIN': 'Cognitive',
            'EXPRESSIVE': 'Expressive Language',
            'EXPRESSIVE_LANGUAGE': 'Expressive Language',
            'RECEPTIVE': 'Receptive Language',
            'RECEPTIVE_LANGUAGE': 'Receptive Language',
            'SOCIAL': 'Social-Emotional',
            'SOCIAL_EMOTIONAL': 'Social-Emotional'
        }

        grouped_evaluations = {}
        for evaluation in evaluations:
            print(f"\nProcessing evaluation ID: {evaluation.id}")
            print(f"Evaluation type: {evaluation.evaluation_type}")
            print(f"Scores: {evaluation.first_eval_score}/{evaluation.second_eval_score}/{evaluation.third_eval_score}")
            
            eval_type = evaluation.evaluation_type
            display_name = evaluation_type_mapping.get(eval_type, eval_type)
            
            if eval_type not in grouped_evaluations:
                grouped_evaluations[eval_type] = {
                    'name': display_name,
                    'evaluations': [],
                    'form_data': form_data_mapping.get(eval_type, {})
                }
            
            # Handle the evaluation data
            try:
                if evaluation.data:
                    print(f"Raw data type: {type(evaluation.data)}")
                    print(f"Raw data content: {evaluation.data}")
                    
                    # If data is a string, try to parse it as JSON
                    if isinstance(evaluation.data, str):
                        try:
                            evaluation.data = json.loads(evaluation.data)
                            print("Successfully parsed string data as JSON")
                        except json.JSONDecodeError as e:
                            print(f"Error decoding JSON: {str(e)}")
                            evaluation.data = {
                                'rows': [],
                                'notes': f'Error: Could not load evaluation data - {str(e)}'
                            }
                    
                    # Ensure the data has the expected structure
                    if isinstance(evaluation.data, dict):
                        if 'rows' not in evaluation.data:
                            print("Adding empty rows list to data")
                            evaluation.data['rows'] = []
                        if 'notes' not in evaluation.data:
                            print("Adding empty notes to data")
                            evaluation.data['notes'] = ''
                    else:
                        print(f"Unexpected data type: {type(evaluation.data)}")
                        evaluation.data = {
                            'rows': [],
                            'notes': 'Error: Invalid data format'
                        }
                else:
                    print("No data found, creating empty structure")
                    evaluation.data = {
                        'rows': [],
                        'notes': ''
                    }
                
                # Debug print the processed data
                print(f"Processed data structure:")
                print(f"Number of rows: {len(evaluation.data.get('rows', []))}")
                print(f"Has notes: {'notes' in evaluation.data}")
                
            except Exception as e:
                print(f"Error processing evaluation data: {str(e)}")
                evaluation.data = {
                    'rows': [],
                    'notes': f'Error processing evaluation data: {str(e)}'
                }

            grouped_evaluations[eval_type]['evaluations'].append(evaluation)

        # Sort evaluations within each group by date
        for eval_type in grouped_evaluations:
            grouped_evaluations[eval_type]['evaluations'].sort(
                key=lambda x: x.created_at, reverse=True
            )

        context = {
            'student': student,
            'grouped_evaluations': grouped_evaluations,
        }

        return render(request, 'view_teacher_evaluations.html', context)

    except Exception as e:
        print(f"Error in view_teacher_evaluations: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, f"An error occurred while loading the evaluations: {str(e)}")
        return redirect('dashboard')

@login_required
def get_evaluation_data(request):
    """
    API view to get evaluation data for a specific evaluation type and child.
    """
    try:
        evaluation_type = request.GET.get('evaluation_type')
        child_name = request.GET.get('child_name')

        if not evaluation_type or not child_name:
            return JsonResponse({
                'status': 'error',
                'message': 'Missing required parameters'
            }, status=400)

        # Debug print
        print(f"Fetching evaluation for type: {evaluation_type}, child: {child_name}")

        # Get the evaluation data
        evaluation = EvaluationDataTeacher.objects.filter(
            child_name=child_name,
            evaluation_type=evaluation_type,
            evaluator_type='TEACHER'
        ).first()

        if not evaluation:
            return JsonResponse({
                'status': 'error',
                'message': 'No evaluation found'
            }, status=404)

        # Debug print
        print(f"Found evaluation: {evaluation.id}")
        print(f"Raw data: {evaluation.data}")

        # Ensure evaluation.data has the expected structure
        evaluation_data = evaluation.data
        if isinstance(evaluation_data, str):
            try:
                evaluation_data = json.loads(evaluation_data)
            except json.JSONDecodeError:
                evaluation_data = {
                    'rows': [],
                    'notes': 'Error: Could not parse evaluation data'
                }
        
        if not isinstance(evaluation_data, dict):
            evaluation_data = {
                'rows': [],
                'notes': 'Error: Invalid data format'
            }
        
        if 'rows' not in evaluation_data:
            evaluation_data['rows'] = []
        if 'notes' not in evaluation_data:
            evaluation_data['notes'] = ''

        # Return the evaluation data
        response_data = {
            'status': 'success',
            'evaluation': {
                'first_eval_score': evaluation.first_eval_score,
                'second_eval_score': evaluation.second_eval_score,
                'third_eval_score': evaluation.third_eval_score,
                'data': evaluation_data,
                'created_at': evaluation.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        }

        # Debug print
        print(f"Sending response: {response_data}")

        return JsonResponse(response_data)

    except Exception as e:
        print(f"Error in get_evaluation_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


from django.shortcuts import render
from .models import EvaluationData, EvaluationDataTeacher
from django.db.models import Sum

def average_evaluation_scores(request):
    # Get all scores from EvaluationData
    evaluation_data_scores = EvaluationData.objects.aggregate(
        first_eval_score_sum=Sum('first_eval_score'),
        second_eval_score_sum=Sum('second_eval_score'),
        third_eval_score_sum=Sum('third_eval_score')
    )

    # Get all scores from EvaluationDataTeacher
    evaluation_data_teacher_scores = EvaluationDataTeacher.objects.aggregate(
        first_eval_score_sum=Sum('first_eval_score'),
        second_eval_score_sum=Sum('second_eval_score'),
        third_eval_score_sum=Sum('third_eval_score')
    )

    # Calculate total scores
    total_first_eval_score = (evaluation_data_scores['first_eval_score_sum'] or 0) + \
                              (evaluation_data_teacher_scores['first_eval_score_sum'] or 0)
    total_second_eval_score = (evaluation_data_scores['second_eval_score_sum'] or 0) + \
                               (evaluation_data_teacher_scores['second_eval_score_sum'] or 0)
    total_third_eval_score = (evaluation_data_scores['third_eval_score_sum'] or 0) + \
                             (evaluation_data_teacher_scores['third_eval_score_sum'] or 0)

    # Calculate average scores
    total_scores_count = 2  # Since we have two models
    average_first_eval_score = total_first_eval_score / total_scores_count if total_scores_count > 0 else 0
    average_second_eval_score = total_second_eval_score / total_scores_count if total_scores_count > 0 else 0
    average_third_eval_score = total_third_eval_score / total_scores_count if total_scores_count > 0 else 0

    context = {
        'average_first_eval_score': average_first_eval_score,
        'average_second_eval_score': average_second_eval_score,
        'average_third_eval_score': average_third_eval_score,
    }

    return render(request, 'TDash.html', context)
