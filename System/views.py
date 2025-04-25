from django.shortcuts import render, redirect, get_object_or_404
from .models import (
    Student, EvaluationRecord, CognitiveEvaluation, ExpressiveEvaluation, 
    FineEvaluation, GrossEvaluation, ReceptiveEvaluation, SelfHelpEvaluation, 
    ParentSelfHelpEvaluation, ParentGrossEvaluation, ParentSocialEvaluation, 
    ParentExpressiveEvaluation, ParentCognitiveEvaluation, Announcement, 
    EvaluationPDF, PDFFile, GrossMotorPDF, SelfHelpPDF, SocialPDF, ExpressivePDF,
    CognitivePDF, GrossMotorPDFTeacher, FinePDFTeacher, CognitivePDFTeacher, SelfHelpPDFTeacher,
    ReceptivePDFTeacher, ExpressivePDFTeacher
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

        # Create the cognitive evaluation record
        CognitiveEvaluation.objects.create(
            student_name=student_name,
            eval1_score=eval1_score,
            eval2_score=eval2_score,
            eval3_score=eval3_score
        )

        # Generate PDF and save to CognitivePDFTeacher model
        try:
            # Create BytesIO buffer to receive PDF data
            buffer = BytesIO()
            
            # Create a PDF using ReportLab
            doc = SimpleDocTemplate(
                buffer, 
                pagesize=landscape(letter),
                topMargin=30,
                leftMargin=30,
                rightMargin=30,
                bottomMargin=30
            )
            elements = []
            
            # Define styles
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
                leading=14,
                spaceBefore=6,
                spaceAfter=6
            )
            header_style = ParagraphStyle(
                'TableHeader',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.white,
                alignment=1,
                fontName='Helvetica-Bold'
            )
            cell_style = ParagraphStyle(
                'TableCell',
                parent=styles['Normal'],
                fontSize=10,
                leading=14,
                wordWrap='CJK'
            )
            checkmark_style = ParagraphStyle(
                'Checkmark',
                parent=styles['Normal'],
                fontSize=12,
                leading=14,
                alignment=1,  # Center alignment
                textColor=colors.black
            )
            
            # Add title
            elements.append(Paragraph(f"Cognitive Evaluation", title_style))
            elements.append(Spacer(1, 5))
            elements.append(Paragraph(f"Student: {student_name}", subtitle_style))
            elements.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", normal_style))
            elements.append(Spacer(1, 15))
            
            # Define evaluation items
            evaluation_items = [
                {
                    'number': '1',
                    'item': 'Looks in the direction of fallen object',
                    'procedure': 'MATERIAL: spoon/ball<br/>PROCEDURE:<br/>With the child seated, get his attention and drop a spoon/ball in front of him. Then observe if his eyes look down as it falls.<br/>Credit if the child can bring his eyes and head down as the objects falls. Automatically credit if item 8.5 is passed.'
                },
                {
                    'number': '2',
                    'item': 'Looks for a partially hidden object',
                    'procedure': 'MATERIALS: spoon/ball<br/>PROCEDURE:<br/>With the child facing you, partially hide a ball behind a small towel and observe if he will look for it and find it. Credit if the child pulls the towel and gets the hidden ball. Automatically credit if item 8.5 is passed.'
                },
                {
                    'number': '3',
                    'item': 'Looks for a completely hidden object',
                    'procedure': 'MATERIALS: ball, small towel/cloth<br/>PROCEDURE:<br/>With the child facing you, hide a ball completely under a small towel and observe if he will look under the towel. Credit if he looks under the towel and gets the hidden ball.'
                },
                {
                    'number': '4',
                    'item': 'Exhibits simple "pretend" play (feeds, puts doll to sleep)',
                    'procedure': 'MATERIAL: doll or toy car/block<br/>PROCEDURE:<br/>If the child is a girl, carry the doll and pretend to rock it to sleep. If the child is a boy, move the car/block back and forth. Credit if the child can imitate this.'
                },
                {
                    'number': '5',
                    'item': 'Matches Objects',
                    'procedure': 'MATERIALS: pairs of spoons, ball, blocks<br/>PROCEDURE:<br/>Place 1 spoon, 1 ball and 1 block of the table. Give the child the other sets of objects arranged in random order. Demonstrate a matching response (e.g., spoon with spoon), then return the object to the child. Say, "Put each one on the one that is just like it." Credit if the child can match the objects correctly.'
                },
                {
                    'number': '6',
                    'item': 'Matches 2 to 3 colors',
                    'procedure': 'MATERIALS: 3 pairs of crayons (blue, red, yellow)<br/>PROCEDURE:<br/>Place 1 crayon of each color on the table of flat surface. Give the child other crayons arranged in random order. Demonstrate a matching response (e.g., red crayon with another red crayon) then return the crayon to the child. Credit if the child can match all the colors correctly.'
                },
                {
                    'number': '7',
                    'item': 'Match picture',
                    'procedure': 'MATERIALS: 3 pairs of picture cards (e.g., pictures of an apple, orange, banana)<br/>PROCEDURE:<br/>Place one copy of each picture on the table or flat surface. Give the child the other pictures arranged in random order. Demonstrate a matching response (e.g., pictures of an apple with another apple) then return the picture to the child. Say, "Put each picture on the one that is just like it." Credit if the child can match all the pictures correctly.'
                },
                {
                    'number': '8',
                    'item': 'Sorts based shapes',
                    'procedure': 'MATERIALS: 4 pairs of different shapes that are of the same size and color<br/>PROCEDURE: Show the child the shapes. Tell the child, "Put together the ones that are the same". Point to the first circle and discuss the shape. Point to the ones with the same shape and ask, "Why did you put these together?" Credit if the child can group the same shapes and say why they are the same (e.g., pareho sila, pareho sila bilog/share, pareho sila kulay).'
                },
                {
                    'number': '9',
                    'item': 'Sorts Object based on 2 attributes (e.g., size and color)',
                    'procedure': 'MATERIALS: 4 pairs of same shapes that differ in size and color, 2 sizes, 2 colors<br/>PROCEDURE:<br/>Show the child the shapes. Tell the child, "Put together the ones that are the same". Credit if the child can sort all the shapes according to size and color.'
                },
                {
                    'number': '10',
                    'item': 'Arranges objects according to size from smallest to biggest',
                    'procedure': 'MATERIALS: 4 pieces of graduated sized squares and 4 pieces of graduated size circle<br/>PROCEDURES: Show the child the first set of squares spread them out random on the table or flat surface. Say, "Here are 4 squares. Look, I can begin with the smallest, then move to the next big one, until I reach the biggest one." Demonstrate how to arrange the squares. The examiner then mixes these and tell the child, "Now you start with the smallest, put the next one and the next big one until the last one".<br/>Repeat these procedures using the circles without demonstrating. Credits if the child arranges at least one set of shapes in correct order from smallest to biggest. Allow one trial for each set of shapes.'
                },
                {
                    'number': '11',
                    'item': 'Name 4 to 6 colors',
                    'procedure': 'MATERIALS: 6 pieces of different colors<br/>PROCEDURE: Ask the child, "What color is this?" Credit if the child can name 4 to 6 colors correctly.'
                },
                {
                    'number': '12',
                    'item': 'Copies shapes',
                    'procedure': 'MATERIALS: paper and pen/crayons<br/>PROCEDURE: Let the child copy a circle and triangle and square after demonstrating how each of these is done.<br/>Credit if the child can name 3 animals or vegetables.'
                },
                {
                    'number': '13',
                    'item': 'Name 3 animals or vegetables when asked',
                    'procedure': 'Credit if the child can name 3 animals or vegetables.'
                },
                {
                    'number': '14',
                    'item': 'States what common household items are used for',
                    'procedure': 'Credit if he can state the use or function of at least 2 household items like a bed and utensils/glass.'
                },
                {
                    'number': '15',
                    'item': 'Can assemble simple puzzles',
                    'procedure': 'MATERIALS: Simple 4 – to 6 – piece puzzles<br/>PROCEDURE: Allow the child to solve the puzzle in 2 minutes. Proceed to the next item after 2 minutes.'
                },
                {
                    'number': '16',
                    'item': 'Demonstrates an understanding of opposites by completing a statement',
                    'procedure': 'Credit if the child can give an opposite word.'
                },
                {
                    'number': '17',
                    'item': 'Points to left and right sides of body',
                    'procedure': 'PROCEDURE: Sit across the child and say "Show me your left hand". Do the same for the following: Right hand, left foot, right knee, left leg. Credit if the child can correctly point out the left and right side of at least 5 body parts as requested.'
                },
                {
                    'number': '18',
                    'item': 'Can state what is silly or wrong with pictures',
                    'procedure': 'MATERIALS: 2 picture cards depicting activities that have something silly or wrong with them<br/>PROCEDURE: Show the pictured scene to the child one at a time and ask, "What is wrong with this picture?" Credit if the child correctly identifies what made the picture incorrect.'
                },
                {
                    'number': '19',
                    'item': 'Matches upper case letters, and matches lower case letters',
                    'procedure': 'MATERIALS: 2 set of alphabet cards with upper- and lower-case letters<br/>PROCEDURE: Randomly present 4 pairs of upper-case letters. Have the child match these. Do the same with 4 pairs, regardless of whether these are upper or lower case.<br/>Note: The child does not have to know the names o the letters.'
                }
            ]
            
            # Create table data
            data = [
                [
                    Paragraph("No.", header_style),
                    Paragraph("Cognitive", header_style),
                    Paragraph("Material/Procedure", header_style),
                    Paragraph("1st Eval", header_style),
                    Paragraph("2nd Eval", header_style),
                    Paragraph("3rd Eval", header_style)
                ]
            ]
            
            # Get checkbox states from the form
            checkboxes = {}
            for i in range(1, 20):  # 19 evaluation items
                eval1 = request.POST.get(f'checkbox_{i}_eval1') == '1'
                eval2 = request.POST.get(f'checkbox_{i}_eval2') == '1'
                eval3 = request.POST.get(f'checkbox_{i}_eval3') == '1'
                checkboxes[i] = [eval1, eval2, eval3]
            
            # Add rows for each evaluation item
            for item in evaluation_items:
                item_num = int(item['number'])
                data.append([
                    Paragraph(item['number'], cell_style),
                    Paragraph(item['item'], cell_style),
                    Paragraph(item['procedure'], cell_style),
                    Paragraph('✓' if checkboxes.get(item_num, [False])[0] else '', checkmark_style),
                    Paragraph('✓' if checkboxes.get(item_num, [False, False])[1] else '', checkmark_style),
                    Paragraph('✓' if checkboxes.get(item_num, [False, False, False])[2] else '', checkmark_style)
                ])
            
            # Add total score row
            data.append([
                Paragraph("", cell_style),
                Paragraph("TOTAL SCORE", ParagraphStyle('Total', parent=cell_style, fontName='Helvetica-Bold')),
                Paragraph("", cell_style),
                Paragraph(str(eval1_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                Paragraph(str(eval2_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                Paragraph(str(eval3_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold'))
            ])
            
            # Define column widths proportionally to the page width
            col_widths = [40, 150, 300, 50, 50, 50]
            
            # Create table
            table = Table(data, colWidths=col_widths)
            
            # Style the table
            green_color = colors.Color(0.176, 0.416, 0.31)  # #2d6a4f in RGB
            light_green = colors.Color(0.925, 0.965, 0.945)  # Very light green for alternating rows
            
            table_style = TableStyle([
                # Header row styling
                ('BACKGROUND', (0, 0), (-1, 0), green_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                
                # Alternating row colors
                *[('BACKGROUND', (0, i), (-1, i), light_green) for i in range(2, len(data)-1, 2)],
                
                # Total row styling
                ('BACKGROUND', (0, -1), (-1, -1), colors.white),
                ('SPAN', (0, -1), (2, -1)),  # Span TOTAL SCORE across first three columns
                
                # Align checkmarks and scores to center
                ('ALIGN', (3, 1), (-1, -1), 'CENTER'),
                
                # Borders
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BOX', (0, 0), (-1, -1), 2, colors.black),
                
                # Cell padding
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ])
            
            # Apply the style
            table.setStyle(table_style)
            elements.append(table)
            
            # Add signature line
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
            
            # Build the PDF
            doc.build(elements)
            
            # Get the PDF value from the buffer
            pdf_value = buffer.getvalue()
            buffer.close()
            
            # Generate a unique filename
            filename = f"cognitive_teacher_{student_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            # Save to CognitivePDFTeacher model
            pdf_record = CognitivePDFTeacher(
                student_name=student_name,
                eval1_score=eval1_score,
                eval2_score=eval2_score,
                eval3_score=eval3_score
            )
            pdf_record.file.save(filename, ContentFile(pdf_value), save=True)
            
        except Exception as e:
            # Log the error but continue with the redirect
            print(f"Error generating PDF: {str(e)}")
            import traceback
            traceback.print_exc()

        messages.success(request, 'Evaluation submitted successfully!')
        return redirect('dashboard')

    return redirect('dashboard')

def submit_expressive_evaluation(request):
    if request.method == 'POST':
        student_name = request.POST.get('student_name')
        eval1_score = int(request.POST.get('eval1_score', 0) or 0)
        eval2_score = int(request.POST.get('eval2_score', 0) or 0)
        eval3_score = int(request.POST.get('eval3_score', 0) or 0)

        # Create the expressive evaluation record
        ExpressiveEvaluation.objects.create(
            student_name=student_name,
            eval1_score=eval1_score,
            eval2_score=eval2_score,
            eval3_score=eval3_score
        )

        # Generate PDF and save to ExpressivePDFTeacher model
        try:
            # Create BytesIO buffer to receive PDF data
            buffer = BytesIO()
            
            # Create a PDF using ReportLab
            doc = SimpleDocTemplate(
                buffer, 
                pagesize=landscape(letter),
                topMargin=30,
                leftMargin=30,
                rightMargin=30,
                bottomMargin=30
            )
            elements = []
            
            # Define styles
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
                leading=14,
                spaceBefore=6,
                spaceAfter=6
            )
            header_style = ParagraphStyle(
                'TableHeader',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.white,
                alignment=1,
                fontName='Helvetica-Bold'
            )
            cell_style = ParagraphStyle(
                'TableCell',
                parent=styles['Normal'],
                fontSize=10,
                leading=14,
                wordWrap='CJK'
            )
            checkmark_style = ParagraphStyle(
                'Checkmark',
                parent=styles['Normal'],
                fontSize=14,  # Increased font size for better visibility
                leading=14,
                alignment=1,  # Center alignment
                textColor=colors.black
            )
            
            # Add title
            elements.append(Paragraph(f"Expressive Language Evaluation", title_style))
            elements.append(Spacer(1, 5))
            elements.append(Paragraph(f"Student: {student_name}", subtitle_style))
            elements.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", normal_style))
            elements.append(Spacer(1, 15))
            
            # Define evaluation items
            evaluation_items = [
                {
                    'number': '1',
                    'item': 'Uses 5 to 20 recognizable words',
                    'procedure': 'PROCEDURE:<br/>Ask the caregiver if the child can clearly say 5 to 6 words aside from "mama" and "papa". This will be the minimum number.'
                },
                {
                    'number': '2',
                    'item': 'Names object in pictures',
                    'procedure': 'MATERIAL: picture book 2<br/>PROCEDURE:<br/>Show the child a picture book, point to an object in the book, then ask him to name it (e.g., "Ano \'to?"). Credit if the child can say the correct name of at least 4 objects.'
                }
            ]
            
            # Create table data
            data = [
                [
                    Paragraph("No.", header_style),
                    Paragraph("Expressive Language", header_style),
                    Paragraph("Material/Procedure", header_style),
                    Paragraph("1st Eval", header_style),
                    Paragraph("2nd Eval", header_style),
                    Paragraph("3rd Eval", header_style)
                ]
            ]
            
            # Get checkbox states from the form
            checkboxes = {}
            for i in range(1, 3):  # 2 evaluation items
                # Get checkbox states directly from the POST data
                eval1 = request.POST.get(f'checkbox_{i}_eval1', '') == 'on'
                eval2 = request.POST.get(f'checkbox_{i}_eval2', '') == 'on'
                eval3 = request.POST.get(f'checkbox_{i}_eval3', '') == 'on'
                checkboxes[i] = [eval1, eval2, eval3]
            
            # Add rows for each evaluation item
            for item in evaluation_items:
                item_num = int(item['number'])
                data.append([
                    Paragraph(item['number'], cell_style),
                    Paragraph(item['item'], cell_style),
                    Paragraph(item['procedure'], cell_style),
                    Paragraph('✓' if checkboxes.get(item_num, [False])[0] else '', checkmark_style),
                    Paragraph('✓' if checkboxes.get(item_num, [False, False])[1] else '', checkmark_style),
                    Paragraph('✓' if checkboxes.get(item_num, [False, False, False])[2] else '', checkmark_style)
                ])
            
            # Add total score row
            data.append([
                Paragraph("", cell_style),
                Paragraph("TOTAL SCORE", ParagraphStyle('Total', parent=cell_style, fontName='Helvetica-Bold')),
                Paragraph("", cell_style),
                Paragraph(str(eval1_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                Paragraph(str(eval2_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                Paragraph(str(eval3_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold'))
            ])
            
            # Define column widths proportionally to the page width
            col_widths = [40, 150, 300, 50, 50, 50]
            
            # Create table
            table = Table(data, colWidths=col_widths)
            
            # Style the table
            green_color = colors.Color(0.176, 0.416, 0.31)  # #2d6a4f in RGB
            light_green = colors.Color(0.925, 0.965, 0.945)  # Very light green for alternating rows
            
            table_style = TableStyle([
                # Header row styling
                ('BACKGROUND', (0, 0), (-1, 0), green_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                
                # Alternating row colors
                *[('BACKGROUND', (0, i), (-1, i), light_green) for i in range(2, len(data)-1, 2)],
                
                # Total row styling
                ('BACKGROUND', (0, -1), (-1, -1), colors.white),
                ('SPAN', (0, -1), (2, -1)),  # Span TOTAL SCORE across first three columns
                
                # Align checkmarks and scores to center
                ('ALIGN', (3, 1), (-1, -1), 'CENTER'),
                
                # Borders
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BOX', (0, 0), (-1, -1), 2, colors.black),
                
                # Cell padding
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ])
            
            # Apply the style
            table.setStyle(table_style)
            elements.append(table)
            
            # Add signature line
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
            
            # Build the PDF
            doc.build(elements)
            
            # Get the PDF value from the buffer
            pdf_value = buffer.getvalue()
            buffer.close()
            
            # Generate a unique filename
            filename = f"expressive_teacher_{student_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            # Save to ExpressivePDFTeacher model
            pdf_record = ExpressivePDFTeacher(
                student_name=student_name,
                eval1_score=eval1_score,
                eval2_score=eval2_score,
                eval3_score=eval3_score
            )
            pdf_record.file.save(filename, ContentFile(pdf_value), save=True)
            
        except Exception as e:
            # Log the error but continue with the redirect
            print(f"Error generating PDF: {str(e)}")
            import traceback
            traceback.print_exc()

        messages.success(request, 'Evaluation submitted successfully!')
        return redirect('dashboard')

    return redirect('dashboard')

def submit_fine_evaluation(request):
    if request.method == 'POST':
        student_name = request.POST.get('student_name')
        eval1_score = int(request.POST.get('eval1_score', 0) or 0)
        eval2_score = int(request.POST.get('eval2_score', 0) or 0)
        eval3_score = int(request.POST.get('eval3_score', 0) or 0)

        # Create the fine motor evaluation record
        FineEvaluation.objects.create(
            student_name=student_name,
            eval1_score=eval1_score,
            eval2_score=eval2_score,
            eval3_score=eval3_score
        )

        # Generate PDF and save to FinePDFTeacher model
        try:
            # Create BytesIO buffer to receive PDF data
            buffer = BytesIO()
            
            # Create a PDF using ReportLab
            doc = SimpleDocTemplate(
                buffer, 
                pagesize=landscape(letter),
                topMargin=30,
                leftMargin=30,
                rightMargin=30,
                bottomMargin=30
            )
            elements = []
            
            # Define styles
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
                leading=14,
                spaceBefore=6,
                spaceAfter=6
            )
            header_style = ParagraphStyle(
                'TableHeader',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.white,
                alignment=1,
                fontName='Helvetica-Bold'
            )
            cell_style = ParagraphStyle(
                'TableCell',
                parent=styles['Normal'],
                fontSize=10,
                leading=14,
                wordWrap='CJK'
            )
            checkmark_style = ParagraphStyle(
                'Checkmark',
                parent=styles['Normal'],
                fontSize=12,
                leading=14,
                alignment=1,  # Center alignment
                textColor=colors.black
            )
            
            # Add title
            elements.append(Paragraph(f"Fine Motor Evaluation", title_style))
            elements.append(Spacer(1, 5))
            elements.append(Paragraph(f"Student: {student_name}", subtitle_style))
            elements.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", normal_style))
            elements.append(Spacer(1, 15))
            
            # Define evaluation items
            evaluation_items = [
                {
                    'number': '1',
                    'item': 'Uses all 5 fingers to get food/toys placed on a flat surface',
                    'procedure': 'MATERIAL: any small toy or food<br/>PROCEDURE:<br/>Seat the child on his/her\'s lap with his elbows at a level with the table top and his hands on the table or flat surface. Put the small toy in front of him and attract his attention by pointing to the toy or tapping the table/flat surface. Credit if the child picks up the toy, using all five fingers as if raking. Automatically credit if he passes the next item.'
                },
                {
                    'number': '2',
                    'item': 'Picks up object with thumb and index finger',
                    'procedure': 'MATERIAL: any small toy or food<br/>PROCEDURE:<br/>Place a toy/food in front of the child and within his reach. Attract his attention by tapping near the toy/food. Credits if the child uses the tips thumb and index or forefinger to pick up the toy/food.'
                },
                {
                    'number': '3',
                    'item': 'Displays a definite hand preference',
                    'procedure': 'MATERIAL: toy<br/>PROCEDURE:<br/>Place the toy directly in front of the child midline (not to his left or his right) and ask him to reach for this. Credit if he uses the same hand 2 out of 3 times. Parental report will suffice.'
                },
                {
                    'number': '4',
                    'item': 'Put small objects in/out of containers',
                    'procedure': 'MATERIAL: small objects, containers<br/>This must be elicited by the interviewer.'
                },
                {
                    'number': '5',
                    'item': 'Holds crayon with all the fingers of his hand as though making a fist (i.e., palmar grasp)',
                    'procedure': 'MATERIAL: crayon<br/>PROCEDURE:<br/>Present the child with a crayon and have him get this. Credits if he holds it by wrapping all five fingers around as if making a fist. Automatically credit if he uses the tips of all five fingers or his thumb, index and middle fingers. This must be elicited by the interviewer.'
                },
                {
                    'number': '6',
                    'item': 'Unscrew the lid of a container or unwraps food',
                    'procedure': 'MATERIAL: container with screw on top or wrapped candy. This must be elicited by the interviewer.'
                },
                {
                    'number': '7',
                    'item': 'Scribbles spontaneously',
                    'procedure': 'MATERIAL: paper, pencil/crayon<br/>PROCEDURE:<br/>Place a piece of paper and pencil/crayon on the table and ask the child to draw anything he wants without showing him what to do. Credit if the child uses the tips of his thumb and any of his thumb and any of his other fingers fingertips to grasp the pencil/crayon and purposefully scribbles on the paper (not accidentally).'
                },
                {
                    'number': '8',
                    'item': 'Scribbles vertical and horizontal lines',
                    'procedure': 'MATERIALS: paper, pencil/crayon<br/>PROCEDURE:<br/>Place a piece paper and pencil/crayon on the table or flat surface and ask the child to draw vertical and horizontal lines after you have demonstrated these to him. Credit if the child produces a vertical or horizontal line that is at least 2 inches long and does not deviate or vary from your vertical line by more than 30 degrees. The lines may be wavy but not broken.'
                },
                {
                    'number': '9',
                    'item': 'Draw Circle purposely',
                    'procedure': 'MATERIALS: paper, pencil/crayon<br/>PROCEDURE:<br/>Place a paper and pencil/crayon on the table or flat surface and ask the child to draw a circle or a ball after you have demonstrated it to him. Credit if the child produces any curve that is closed or nearly closed. Continuous spiral motions are not credited.'
                },
                {
                    'number': '10',
                    'item': 'Draws a human figure (head, eyes, trunk, arms, hands/fingers)',
                    'procedure': 'MATERIAL: paper, pencil<br/>PROCEDURE:<br/>Give the child a pencil and a paper and ask him to draw a picture of a person. Credit if the child has drawn 3 or more body parts. A pair is considered one part (eyes, ears, arms, hands, legs and feet) and must be drawn in pairs to get full credit unless the drawing is in profile.'
                },
                {
                    'number': '11',
                    'item': 'Draws a house using geometric forms',
                    'procedure': 'MATERIALS: Paper, pencil<br/>PROCEDURE:<br/>Give the child a pencil a pencil and paper and ask him to draw a picture of a house. Credit if the child has drawn at least the roof, main frame, and a door or window.'
                }
            ]
            
            # Create table data
            data = [
                [
                    Paragraph("No.", header_style),
                    Paragraph("Fine Motor", header_style),
                    Paragraph("Material/Procedure", header_style),
                    Paragraph("1st Eval", header_style),
                    Paragraph("2nd Eval", header_style),
                    Paragraph("3rd Eval", header_style)
                ]
            ]
            
            # Get checkbox states from the form
            checkboxes = {}
            for i in range(1, 12):  # 11 evaluation items
                eval1 = request.POST.get(f'checkbox_{i}_eval1') == '1'
                eval2 = request.POST.get(f'checkbox_{i}_eval2') == '1'
                eval3 = request.POST.get(f'checkbox_{i}_eval3') == '1'
                checkboxes[i] = [eval1, eval2, eval3]
            
            # Add rows for each evaluation item
            for item in evaluation_items:
                item_num = int(item['number'])
                data.append([
                    Paragraph(item['number'], cell_style),
                    Paragraph(item['item'], cell_style),
                    Paragraph(item['procedure'], cell_style),
                    Paragraph('✓' if checkboxes.get(item_num, [False])[0] else '', checkmark_style),
                    Paragraph('✓' if checkboxes.get(item_num, [False, False])[1] else '', checkmark_style),
                    Paragraph('✓' if checkboxes.get(item_num, [False, False, False])[2] else '', checkmark_style)
                ])
            
            # Add total score row
            data.append([
                Paragraph("", cell_style),
                Paragraph("TOTAL SCORE", ParagraphStyle('Total', parent=cell_style, fontName='Helvetica-Bold')),
                Paragraph("", cell_style),
                Paragraph(str(eval1_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                Paragraph(str(eval2_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                Paragraph(str(eval3_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold'))
            ])
            
            # Define column widths proportionally to the page width
            col_widths = [40, 150, 300, 50, 50, 50]
            
            # Create table
            table = Table(data, colWidths=col_widths)
            
            # Style the table
            green_color = colors.Color(0.176, 0.416, 0.31)  # #2d6a4f in RGB
            light_green = colors.Color(0.925, 0.965, 0.945)  # Very light green for alternating rows
            
            table_style = TableStyle([
                # Header row styling
                ('BACKGROUND', (0, 0), (-1, 0), green_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                
                # Alternating row colors
                *[('BACKGROUND', (0, i), (-1, i), light_green) for i in range(2, len(data)-1, 2)],
                
                # Total row styling
                ('BACKGROUND', (0, -1), (-1, -1), colors.white),
                ('SPAN', (0, -1), (2, -1)),  # Span TOTAL SCORE across first three columns
                
                # Align checkmarks and scores to center
                ('ALIGN', (3, 1), (-1, -1), 'CENTER'),
                
                # Borders
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BOX', (0, 0), (-1, -1), 2, colors.black),
                
                # Cell padding
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ])
            
            # Apply the style
            table.setStyle(table_style)
            elements.append(table)
            
            # Add signature line
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
            
            # Build the PDF
            doc.build(elements)
            
            # Get the PDF value from the buffer
            pdf_value = buffer.getvalue()
            buffer.close()
            
            # Generate a unique filename
            filename = f"fine_motor_teacher_{student_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            # Save to FinePDFTeacher model
            pdf_record = FinePDFTeacher(
                student_name=student_name,
                eval1_score=eval1_score,
                eval2_score=eval2_score,
                eval3_score=eval3_score
            )
            pdf_record.file.save(filename, ContentFile(pdf_value), save=True)
            
        except Exception as e:
            # Log the error but continue with the redirect
            print(f"Error generating PDF: {str(e)}")
            import traceback
            traceback.print_exc()

        messages.success(request, 'Evaluation submitted successfully!')
        return redirect('dashboard')

    return redirect('dashboard')

def submit_gross_evaluation(request):
    if request.method == 'POST':
        student_name = request.POST.get('student_name')
        eval1_score = int(request.POST.get('eval1_score', 0) or 0)
        eval2_score = int(request.POST.get('eval2_score', 0) or 0)
        eval3_score = int(request.POST.get('eval3_score', 0) or 0)

        # Create the gross motor evaluation record
        GrossEvaluation.objects.create(
            student_name=student_name,
            eval1_score=eval1_score,
            eval2_score=eval2_score,
            eval3_score=eval3_score
        )
        
        # Generate PDF and save to GrossMotorPDFTeacher model
        try:
            # Create BytesIO buffer to receive PDF data
            buffer = BytesIO()
            
            # Create a PDF using ReportLab
            doc = SimpleDocTemplate(
                buffer, 
                pagesize=landscape(letter),
                topMargin=30,
                leftMargin=30,
                rightMargin=30,
                bottomMargin=30
            )
            elements = []
            
            # Define styles
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
                leading=14,
                spaceBefore=6,
                spaceAfter=6
            )
            header_style = ParagraphStyle(
                'TableHeader',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.white,
                alignment=1,
                fontName='Helvetica-Bold'
            )
            cell_style = ParagraphStyle(
                'TableCell',
                parent=styles['Normal'],
                fontSize=10,
                leading=14,
                wordWrap='CJK'
            )
            
            # Add a special style for checkboxes
            checkbox_style = ParagraphStyle(
                'Checkbox',
                parent=styles['Normal'],
                fontSize=14,  # Larger font size for checkboxes
                leading=14,
                alignment=1,  # Center alignment
                textColor=colors.black
            )
            
            # Add title
            elements.append(Paragraph(f"Gross Motor Evaluation", title_style))
            elements.append(Spacer(1, 5))
            elements.append(Paragraph(f"Student: {student_name}", subtitle_style))
            elements.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", normal_style))
            elements.append(Spacer(1, 15))
            
            # Define evaluation items
            evaluation_items = [
                {
                    'number': '1',
                    'item': 'Walk backwards',
                    'procedure': 'MATERIAL: toy<br/>PROCEDURE:<br/>Ask the child to walk backwards by demonstrating this. Credit if the child is able to walk backwards without falling and holding anything. Parental report will suffice.'
                },
                {
                    'number': '2',
                    'item': 'Runs without tripping or falling',
                    'procedure': 'MATERIAL: ball<br/>PROCEDURE:<br/>Encourage the child to run by rolling a ball across the floor. Credit if the child can run past and without tripping or falling.'
                },
                {
                    'number': '3',
                    'item': 'Walks upstairs holding onto a handrail, 2 feet on each step',
                    'procedure': 'MATERIAL: toy<br/>PROCEDURE:<br/>Place a toy in the middle of the 4th and 5th step and ask the child to walk up the stairs to get the toy. Credit if the child walks up the stairs using the handrail or wall for support and places both feet on each step before stepping on the next one. Automatically credit if item #6 is passed. Parental report will suffice.'
                },
                {
                    'number': '4',
                    'item': 'Walks upstairs with alternate feet without holding onto a handrail',
                    'procedure': 'MATERIAL: toy<br/>PROCEDURE:<br/>Place a toy in the middle of the 4th and 5th step and ask the child to walk up the stairs to get the toy. Credit if the child walks upstairs, alternating his feet as he steps on each successive step without holding onto the handrail or wall for support. Parental report will suffice.'
                },
                {
                    'number': '5',
                    'item': 'Walks downstairs with alternate feet without holding onto a handrail',
                    'procedure': 'MATERIAL: toy<br/>PROCEDURE:<br/>Place a toy at the bottom of the stairs and ask the child to walk downstairs to get the toy. Credit if the child walks upstairs, alternating his feet as he steps on each successive step without holding onto the handrail or wall for support. Do not give credit if the child places both feet on the step or uses the handrail or wall for support. Parental report will suffice.'
                },
                {
                    'number': '6',
                    'item': 'Moves body part as directed',
                    'procedure': 'PROCEDURE:<br/>Ask the child to raise both arms'
                },
                {
                    'number': '7',
                    'item': 'Jumps up',
                    'procedure': 'This must be elicited by the interviewer.'
                },
                {
                    'number': '8',
                    'item': 'Throws ball overhead with direction',
                    'procedure': 'MATERIAL: ball<br/>PROCEDURE:<br/>Give the child the ball and stand at least 3 feet away from him. Ask the child to throw. You may show the child how to it. Credit if the child throws the ball within you arm\'s reach between your knees and head using an overhand throw and not sideways of underhand.'
                },
                {
                    'number': '9',
                    'item': 'Hops 3 steps on preferred foot',
                    'procedure': 'PROCEDURE:<br/>Ask the child to lift his foot and hot at least 3 times on his preferred foot. Credits if the child is able to hop at least 3 times on his preferred foot without holding on to anything.'
                },
                {
                    'number': '10',
                    'item': 'Jumps and turns',
                    'procedure': 'PROCEDURES:<br/>Ask the child to jump while making a half-turn. Credit if the child is able to do this without tripping or falling.'
                }
            ]
            
            # Create table data
            data = [
                [
                    Paragraph("No.", header_style),
                    Paragraph("Gross Motor", header_style),
                    Paragraph("Material / Procedure", header_style),
                    Paragraph("1st Eval", header_style),
                    Paragraph("2nd Eval", header_style),
                    Paragraph("3rd Eval", header_style)
                ]
            ]
            
            # Get checkbox states from the form
            checkboxes = {}
            for i in range(1, 11):  # 10 evaluation items
                eval1 = request.POST.get(f'checkbox_{i}_eval1') == '1'
                eval2 = request.POST.get(f'checkbox_{i}_eval2') == '1'
                eval3 = request.POST.get(f'checkbox_{i}_eval3') == '1'
                checkboxes[i] = [eval1, eval2, eval3]
            
            # Add rows for each evaluation item
            for item in evaluation_items:
                item_num = int(item['number'])
                data.append([
                    Paragraph(item['number'], cell_style),
                    Paragraph(item['item'], cell_style),
                    Paragraph(item['procedure'], cell_style),
                    Paragraph('✓' if checkboxes.get(item_num, [False])[0] else '', checkbox_style),
                    Paragraph('✓' if checkboxes.get(item_num, [False, False])[1] else '', checkbox_style),
                    Paragraph('✓' if checkboxes.get(item_num, [False, False, False])[2] else '', checkbox_style)
                ])
            
            # Add total score row
            data.append([
                Paragraph("", cell_style),
                Paragraph("TOTAL SCORE", ParagraphStyle('Total', parent=cell_style, fontName='Helvetica-Bold')),
                Paragraph("", cell_style),
                Paragraph(str(eval1_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                Paragraph(str(eval2_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                Paragraph(str(eval3_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold'))
            ])
            
            # Define column widths proportionally to the page width
            col_widths = [40, 150, 300, 50, 50, 50]
            
            # Create table
            table = Table(data, colWidths=col_widths)
            
            # Style the table
            green_color = colors.Color(0.176, 0.416, 0.31)  # #2d6a4f in RGB
            light_green = colors.Color(0.925, 0.965, 0.945)  # Very light green for alternating rows
            
            table_style = TableStyle([
                # Header row styling
                ('BACKGROUND', (0, 0), (-1, 0), green_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                
                # Alternating row colors
                *[('BACKGROUND', (0, i), (-1, i), light_green) for i in range(2, len(data)-1, 2)],
                
                # Total row styling
                ('BACKGROUND', (0, -1), (-1, -1), colors.white),
                ('SPAN', (0, -1), (2, -1)),  # Span TOTAL SCORE across first three columns
                
                # Align checkmarks and scores to center
                ('ALIGN', (3, 1), (-1, -1), 'CENTER'),
                
                # Borders
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BOX', (0, 0), (-1, -1), 2, colors.black),
                
                # Cell padding
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ])
            
            # Apply the style
            table.setStyle(table_style)
            elements.append(table)
            
            # Add signature line
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
            
            # Build the PDF
            doc.build(elements)
            
            # Get the PDF value from the buffer
            pdf_value = buffer.getvalue()
            buffer.close()
            
            # Generate a unique filename
            filename = f"gross_motor_{student_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            # Save to GrossMotorPDFTeacher model
            pdf_record = GrossMotorPDFTeacher(
                student_name=student_name,
                eval1_score=eval1_score,
                eval2_score=eval2_score,
                eval3_score=eval3_score
            )
            pdf_record.file.save(filename, ContentFile(pdf_value), save=True)
            
        except Exception as e:
            # Log the error but continue with the redirect
            print(f"Error generating PDF: {str(e)}")
            import traceback
            traceback.print_exc()

        messages.success(request, 'Evaluation submitted successfully!')
        return redirect('dashboard')  # or wherever you want to redirect after submission

    return redirect('dashboard')

def submit_receptive_evaluation(request):
    if request.method == 'POST':
        student_name = request.POST.get('student_name')
        eval1_score = int(request.POST.get('eval1_score', 0) or 0)
        eval2_score = int(request.POST.get('eval2_score', 0) or 0)
        eval3_score = int(request.POST.get('eval3_score', 0) or 0)

        # Create the receptive evaluation record
        ReceptiveEvaluation.objects.create(
            student_name=student_name,
            eval1_score=eval1_score,
            eval2_score=eval2_score,
            eval3_score=eval3_score
        )

        # Generate PDF and save to ReceptivePDFTeacher model
        try:
            # Create BytesIO buffer to receive PDF data
            buffer = BytesIO()
            
            # Create a PDF using ReportLab
            doc = SimpleDocTemplate(
                buffer, 
                pagesize=landscape(letter),
                topMargin=30,
                leftMargin=30,
                rightMargin=30,
                bottomMargin=30
            )
            elements = []
            
            # Define styles
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
                leading=14,
                spaceBefore=6,
                spaceAfter=6
            )
            header_style = ParagraphStyle(
                'TableHeader',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.white,
                alignment=1,
                fontName='Helvetica-Bold'
            )
            cell_style = ParagraphStyle(
                'TableCell',
                parent=styles['Normal'],
                fontSize=10,
                leading=14,
                wordWrap='CJK'
            )
            checkmark_style = ParagraphStyle(
                'Checkmark',
                parent=styles['Normal'],
                fontSize=14,  # Increased font size for better visibility
                leading=14,
                alignment=1,  # Center alignment
                textColor=colors.black
            )
            
            # Add title
            elements.append(Paragraph(f"Receptive Language Evaluation", title_style))
            elements.append(Spacer(1, 5))
            elements.append(Paragraph(f"Student: {student_name}", subtitle_style))
            elements.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", normal_style))
            elements.append(Spacer(1, 15))
            
            # Define evaluation items
            evaluation_items = [
                {
                    'number': '1',
                    'item': 'Points a family member when she asked to do so',
                    'procedure': 'PROCEDURE:<br/>Ask the child to point to his mother/caregiver.<br/>Credit if he so does.'
                },
                {
                    'number': '2',
                    'item': 'Points to 5 body parts on himself when asked to do so',
                    'procedure': 'PROCEDURE:<br/>Have the child point his eyes, nose, mouth, hands and feet.<br/>Credit if he can point to all these.'
                },
                {
                    'number': '3',
                    'item': 'Points to 5 named pictured object when asked to do so',
                    'procedure': 'MATERIAL: picture book/1<br/>PROCEDURE:<br/>Show the child a picture book (2 pictures per page) and ask him to point to them by saying "Where\'s the _____?" Credit if the child can use his finger to point to at least 5 pictures.'
                },
                {
                    'number': '4',
                    'item': 'Follows one-step instructions that include simple preposition (e.g., in, on, under, etc.)',
                    'procedure': 'MATERIAL: block/toy<br/>PROCEDURE:<br/>Ask the child to put a block/toy under the table on the table, in the bag. Do not point or use gestures when giving the instructions. Credit if the child is able to follow at least one of the instructions.'
                },
                {
                    'number': '5',
                    'item': 'Follows 2-step instructions that include simple prepositions',
                    'procedure': 'MATERIAL: block/toy<br/>PROCEDURE:<br/>Ask the child to get a block/toy from under the table and then place it on the table. Do not point or use gestures when giving the instructions. Credit if the child is able to follow the instructions.'
                }
            ]
            
            # Create table data
            data = [
                [
                    Paragraph("No.", header_style),
                    Paragraph("Receptive Language", header_style),
                    Paragraph("Material/Procedure", header_style),
                    Paragraph("1st Eval", header_style),
                    Paragraph("2nd Eval", header_style),
                    Paragraph("3rd Eval", header_style)
                ]
            ]
            
            # Get checkbox states from the form
            checkboxes = {}
            for i in range(1, 6):  # 5 evaluation items
                # Get checkbox states directly from the POST data
                eval1 = request.POST.get(f'checkbox_{i}_eval1', '') == 'on'
                eval2 = request.POST.get(f'checkbox_{i}_eval2', '') == 'on'
                eval3 = request.POST.get(f'checkbox_{i}_eval3', '') == 'on'
                checkboxes[i] = [eval1, eval2, eval3]
            
            # Add rows for each evaluation item
            for item in evaluation_items:
                item_num = int(item['number'])
                data.append([
                    Paragraph(item['number'], cell_style),
                    Paragraph(item['item'], cell_style),
                    Paragraph(item['procedure'], cell_style),
                    Paragraph('✓' if checkboxes.get(item_num, [False])[0] else '', checkmark_style),
                    Paragraph('✓' if checkboxes.get(item_num, [False, False])[1] else '', checkmark_style),
                    Paragraph('✓' if checkboxes.get(item_num, [False, False, False])[2] else '', checkmark_style)
                ])
            
            # Add total score row
            data.append([
                Paragraph("", cell_style),
                Paragraph("TOTAL SCORE", ParagraphStyle('Total', parent=cell_style, fontName='Helvetica-Bold')),
                Paragraph("", cell_style),
                Paragraph(str(eval1_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                Paragraph(str(eval2_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                Paragraph(str(eval3_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold'))
            ])
            
            # Define column widths proportionally to the page width
            col_widths = [40, 150, 300, 50, 50, 50]
            
            # Create table
            table = Table(data, colWidths=col_widths)
            
            # Style the table
            green_color = colors.Color(0.176, 0.416, 0.31)  # #2d6a4f in RGB
            light_green = colors.Color(0.925, 0.965, 0.945)  # Very light green for alternating rows
            
            table_style = TableStyle([
                # Header row styling
                ('BACKGROUND', (0, 0), (-1, 0), green_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                
                # Alternating row colors
                *[('BACKGROUND', (0, i), (-1, i), light_green) for i in range(2, len(data)-1, 2)],
                
                # Total row styling
                ('BACKGROUND', (0, -1), (-1, -1), colors.white),
                ('SPAN', (0, -1), (2, -1)),  # Span TOTAL SCORE across first three columns
                
                # Align checkmarks and scores to center
                ('ALIGN', (3, 1), (-1, -1), 'CENTER'),
                
                # Borders
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BOX', (0, 0), (-1, -1), 2, colors.black),
                
                # Cell padding
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ])
            
            # Apply the style
            table.setStyle(table_style)
            elements.append(table)
            
            # Add signature line
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
            
            # Build the PDF
            doc.build(elements)
            
            # Get the PDF value from the buffer
            pdf_value = buffer.getvalue()
            buffer.close()
            
            # Generate a unique filename
            filename = f"receptive_teacher_{student_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            # Save to ReceptivePDFTeacher model
            pdf_record = ReceptivePDFTeacher(
                student_name=student_name,
                eval1_score=eval1_score,
                eval2_score=eval2_score,
                eval3_score=eval3_score
            )
            pdf_record.file.save(filename, ContentFile(pdf_value), save=True)
            
        except Exception as e:
            # Log the error but continue with the redirect
            print(f"Error generating PDF: {str(e)}")
            import traceback
            traceback.print_exc()

        messages.success(request, 'Evaluation submitted successfully!')
        return redirect('dashboard')

    return redirect('dashboard')

def submit_selfhelp_evaluation(request):
    if request.method == 'POST':
        student_name = request.POST.get('student_name')
        eval1_score = int(request.POST.get('eval1_score', 0) or 0)
        eval2_score = int(request.POST.get('eval2_score', 0) or 0)
        eval3_score = int(request.POST.get('eval3_score', 0) or 0)

        # Create the self-help evaluation record
        SelfHelpEvaluation.objects.create(
            student_name=student_name,
            eval1_score=eval1_score,
            eval2_score=eval2_score,
            eval3_score=eval3_score
        )

        # Generate PDF and save to SelfHelpPDFTeacher model
        try:
            # Create BytesIO buffer to receive PDF data
            buffer = BytesIO()
            
            # Create a PDF using ReportLab
            doc = SimpleDocTemplate(
                buffer, 
                pagesize=landscape(letter),
                topMargin=30,
                leftMargin=30,
                rightMargin=30,
                bottomMargin=30
            )
            elements = []
            
            # Define styles
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
                leading=14,
                spaceBefore=6,
                spaceAfter=6
            )
            header_style = ParagraphStyle(
                'TableHeader',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.white,
                alignment=1,
                fontName='Helvetica-Bold'
            )
            cell_style = ParagraphStyle(
                'TableCell',
                parent=styles['Normal'],
                fontSize=10,
                leading=14,
                wordWrap='CJK'
            )
            checkmark_style = ParagraphStyle(
                'Checkmark',
                parent=styles['Normal'],
                fontSize=12,
                leading=14,
                alignment=1,  # Center alignment
                textColor=colors.black
            )
            
            # Add title
            elements.append(Paragraph(f"Self-Help Evaluation", title_style))
            elements.append(Spacer(1, 5))
            elements.append(Paragraph(f"Student: {student_name}", subtitle_style))
            elements.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", normal_style))
            elements.append(Spacer(1, 15))
            
            # Define evaluation items
            evaluation_items = [
                {
                    'number': '1',
                    'item': 'Feeds self with finger foods (e.g. biscuits, bread) using fingers',
                    'procedure': 'MATERIALS: bread, biscuits<br/>This must be elicited by the interviewer.'
                },
                {
                    'number': '2',
                    'item': 'Helps hold cup for drinking',
                    'procedure': 'MATERIALS: drinking cup, water<br/>Note: The cup should not have a lid or spout<br/>This must be elicited by the interviewer.'
                },
                {
                    'number': '3',
                    'item': 'Drinks from cup with spillage',
                    'procedure': 'MATERIALS: drinking cup, water<br/>Note: The cup should not have a lid or spout<br/>This must be elicited by the interviewer.<br/>Automatically credits if he passed the next item.'
                },
                {
                    'number': '4',
                    'item': 'Drinks from cup unassisted',
                    'procedure': 'MATERIALS: drinking cup, water<br/>This must be elicited by the interviewer.'
                },
                {
                    'number': '5',
                    'item': 'Prepares own food/snack',
                    'procedure': 'Ask the caregiver if the child can prepare his own snack without help except for getting items that are hard to reach (e.g., bowl, spoon).'
                },
                {
                    'number': '6',
                    'item': 'Dress without assistance, including buttoning and tying',
                    'procedure': 'MATERIAL: small shirt w/ button and shoe w/shoestring<br/>PROCEDURE:<br/>Have the child demonstrate how to button and tie to credit this item.'
                },
                {
                    'number': '7',
                    'item': 'Washes and dries hands without help',
                    'procedure': 'Ask the caregiver if the child can wash and dry his hand without any help or supervision except to turn on/off faucets that are out of reach.'
                },
                {
                    'number': '8',
                    'item': 'Washes face without any help',
                    'procedure': 'Ask the caregiver if the child can wash and dry his face without any help or supervision except to turn on/off faucets that are out of reach.'
                }
            ]
            
            # Create table data
            data = [
                [
                    Paragraph("No.", header_style),
                    Paragraph("Self-Help", header_style),
                    Paragraph("Material/Procedure", header_style),
                    Paragraph("1st Eval", header_style),
                    Paragraph("2nd Eval", header_style),
                    Paragraph("3rd Eval", header_style)
                ]
            ]
            
            # Get checkbox states from the form
            checkboxes = {}
            for i in range(1, 9):  # 8 evaluation items
                eval1 = request.POST.get(f'checkbox_{i}_eval1') == '1'
                eval2 = request.POST.get(f'checkbox_{i}_eval2') == '1'
                eval3 = request.POST.get(f'checkbox_{i}_eval3') == '1'
                checkboxes[i] = [eval1, eval2, eval3]
            
            # Add rows for each evaluation item
            for item in evaluation_items:
                item_num = int(item['number'])
                data.append([
                    Paragraph(item['number'], cell_style),
                    Paragraph(item['item'], cell_style),
                    Paragraph(item['procedure'], cell_style),
                    Paragraph('✓' if checkboxes.get(item_num, [False])[0] else '', checkmark_style),
                    Paragraph('✓' if checkboxes.get(item_num, [False, False])[1] else '', checkmark_style),
                    Paragraph('✓' if checkboxes.get(item_num, [False, False, False])[2] else '', checkmark_style)
                ])
            
            # Add total score row
            data.append([
                Paragraph("", cell_style),
                Paragraph("TOTAL SCORE", ParagraphStyle('Total', parent=cell_style, fontName='Helvetica-Bold')),
                Paragraph("", cell_style),
                Paragraph(str(eval1_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                Paragraph(str(eval2_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                Paragraph(str(eval3_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold'))
            ])
            
            # Define column widths proportionally to the page width
            col_widths = [40, 150, 300, 50, 50, 50]
            
            # Create table
            table = Table(data, colWidths=col_widths)
            
            # Style the table
            green_color = colors.Color(0.176, 0.416, 0.31)  # #2d6a4f in RGB
            light_green = colors.Color(0.925, 0.965, 0.945)  # Very light green for alternating rows
            
            table_style = TableStyle([
                # Header row styling
                ('BACKGROUND', (0, 0), (-1, 0), green_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                
                # Alternating row colors
                *[('BACKGROUND', (0, i), (-1, i), light_green) for i in range(2, len(data)-1, 2)],
                
                # Total row styling
                ('BACKGROUND', (0, -1), (-1, -1), colors.white),
                ('SPAN', (0, -1), (2, -1)),  # Span TOTAL SCORE across first three columns
                
                # Align checkmarks and scores to center
                ('ALIGN', (3, 1), (-1, -1), 'CENTER'),
                
                # Borders
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BOX', (0, 0), (-1, -1), 2, colors.black),
                
                # Cell padding
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ])
            
            # Apply the style
            table.setStyle(table_style)
            elements.append(table)
            
            # Add signature line
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
            
            # Build the PDF
            doc.build(elements)
            
            # Get the PDF value from the buffer
            pdf_value = buffer.getvalue()
            buffer.close()
            
            # Generate a unique filename
            filename = f"self_help_teacher_{student_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            # Save to SelfHelpPDFTeacher model
            pdf_record = SelfHelpPDFTeacher(
                student_name=student_name,
                eval1_score=eval1_score,
                eval2_score=eval2_score,
                eval3_score=eval3_score
            )
            pdf_record.file.save(filename, ContentFile(pdf_value), save=True)
            
        except Exception as e:
            # Log the error but continue with the redirect
            print(f"Error generating PDF: {str(e)}")
            import traceback
            traceback.print_exc()

        messages.success(request, 'Evaluation submitted successfully!')
        return redirect('dashboard')

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
            
            # Get checkbox states
            checkbox_data = []
            for i in range(1, 21):  # 20 evaluation items for self-help
                eval1 = request.POST.get(f'checkbox_{i}_eval1') == '1'
                eval2 = request.POST.get(f'checkbox_{i}_eval2') == '1'
                eval3 = request.POST.get(f'checkbox_{i}_eval3') == '1'
                checkbox_data.append({
                    'number': i,
                    'checked': [eval1, eval2, eval3]
                })
            
            # Get comments if any
            comments = []
            for i in range(1, 21):  # 20 evaluation items
                comment = request.POST.get(f'comment_{i}', '')
                if comment:
                    comments.append({'number': i, 'text': comment})
            
            # Create a new evaluation record
            evaluation = ParentSelfHelpEvaluation(
                student_name=student_name,
                eval1_score=eval1_score,
                eval2_score=eval2_score,
                eval3_score=eval3_score
            )
            evaluation.save()
            
            # Generate PDF
            try:
                # Create BytesIO buffer for PDF
                buffer = BytesIO()
                
                # Create the PDF object using reportlab
                doc = SimpleDocTemplate(
                    buffer,
                    pagesize=landscape(letter),
                    topMargin=20,
                    leftMargin=20,
                    rightMargin=20,
                    bottomMargin=20
                )
                
                # Define styles
                styles = getSampleStyleSheet()
                title_style = ParagraphStyle(
                    'Title',
                    parent=styles['Heading1'],
                    fontSize=16,
                    textColor=colors.darkgreen,
                    alignment=1,
                    spaceAfter=8
                )
                subtitle_style = ParagraphStyle(
                    'Subtitle',
                    parent=styles['Heading2'],
                    fontSize=12,
                    textColor=colors.darkgreen,
                    alignment=1,
                    spaceAfter=4
                )
                normal_style = ParagraphStyle(
                    'Normal',
                    parent=styles['Normal'],
                    fontSize=10,
                    leading=12,
                    spaceBefore=4,
                    spaceAfter=4
                )
                header_style = ParagraphStyle(
                    'TableHeader',
                    parent=styles['Normal'],
                    fontSize=10,
                    textColor=colors.white,
                    alignment=1,
                    fontName='Helvetica-Bold'
                )
                cell_style = ParagraphStyle(
                    'TableCell',
                    parent=styles['Normal'],
                    fontSize=8,
                    leading=10,
                    wordWrap='CJK'
                )
                
                # Create elements list for PDF content
                elements = []
                
                # Add title
                elements.append(Paragraph("Parent Self-Help Evaluation", title_style))
                elements.append(Spacer(1, 5))
                elements.append(Paragraph(f"Student: {student_name}", subtitle_style))
                elements.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", normal_style))
                elements.append(Spacer(1, 10))
                
                # Create table data
                data = [
                    [
                        Paragraph("No.", header_style),
                        Paragraph("Self-Help", header_style),
                        Paragraph("Material/Procedure", header_style),
                        Paragraph("1st", header_style),
                        Paragraph("2nd", header_style),
                        Paragraph("3rd", header_style),
                        Paragraph("Comments", header_style)
                    ]
                ]
                
                # Define evaluation items with all 20 items
                evaluation_items = [
                    {
                        'number': '1',
                        'item': 'Feeding sub-domain',
                        'procedure': 'Parental report will suffice.'
                    },
                    {
                        'number': '2',
                        'item': 'Feed self using fingers to eat non-hands with spoon',
                        'procedure': 'Automatically credit if child eats without spillage. Parental report will suffice.'
                    },
                    {
                        'number': '3',
                        'item': 'Feed self using spoon without spillage',
                        'procedure': 'Automatically credit if child eats without spillage. Parental report will suffice.'
                    },
                    {
                        'number': '4',
                        'item': 'Feed self using fingers without spillage',
                        'procedure': 'Parental report will suffice.'
                    },
                    {
                        'number': '5',
                        'item': 'Feed self using spoon without spillage',
                        'procedure': 'Parental report will suffice.'
                    },
                    {
                        'number': '6',
                        'item': 'Eats with head held for spoon-feeding during any meal',
                        'procedure': 'Parental report will suffice.'
                    },
                    {
                        'number': '7',
                        'item': 'Gets drink for self-unassisted',
                        'procedure': 'Parental report will suffice.'
                    },
                    {
                        'number': '8',
                        'item': 'Pours from pitcher without spillage',
                        'procedure': 'Parental report will suffice.'
                    },
                    {
                        'number': '9',
                        'item': 'Volunteers to help younger siblings/family members when no adult is around',
                        'procedure': 'Parental report will suffice.'
                    },
                    {
                        'number': '10',
                        'item': 'Dressing sub-domain - Self-dresses after being dressed (e.g., raises arms or lift legs)',
                        'procedure': 'Parental report will suffice.'
                    },
                    {
                        'number': '11',
                        'item': 'Pulls down preferred short pants',
                        'procedure': 'Parental report will suffice.'
                    },
                    {
                        'number': '12',
                        'item': 'Removes sando',
                        'procedure': 'Parental report will suffice.'
                    },
                    {
                        'number': '13',
                        'item': 'Dresses without assistance except for buttoning and tying',
                        'procedure': 'Parental report will suffice.'
                    },
                    {
                        'number': '14',
                        'item': 'Toilet Training sub-domain - Informs adult only after he has already urinated (wash) or moved has bowels (pooped) in his underpants',
                        'procedure': 'Parental report will suffice.'
                    },
                    {
                        'number': '15',
                        'item': 'Informs the adult of need to urinate (pee) or move bowels (poop) ahead of time such as through place (e.g., comfort room)',
                        'procedure': 'Parental report will suffice.'
                    },
                    {
                        'number': '16',
                        'item': 'Goes to the designated place to urinate (pee) or move bowels (poop) but sometimes still does this in his underpants',
                        'procedure': 'Parental report will suffice.'
                    },
                    {
                        'number': '17',
                        'item': 'Goes to the designated place to urinate (pee) or move bowels (poop) and never does this in his underpants',
                        'procedure': 'Parental report will suffice.'
                    },
                    {
                        'number': '18',
                        'item': 'Wipes/cleans self after a bowel movement (poop)',
                        'procedure': 'Parental report will suffice.'
                    },
                    {
                        'number': '19',
                        'item': 'Bathing sub-domain - Participates when bathing (e.g., putting on soap)',
                        'procedure': 'Parental report will suffice.'
                    },
                    {
                        'number': '20',
                        'item': 'Bathes without any help',
                        'procedure': 'Parental report will suffice.'
                    }
                ]
                
                # Add rows for each evaluation item
                for item in evaluation_items:
                    item_num = int(item['number'])
                    checkbox_state = next((x for x in checkbox_data if x['number'] == item_num), None)
                    comment = next((x for x in comments if x['number'] == item_num), {'text': ''})
                    
                    data.append([
                        Paragraph(item['number'], cell_style),
                        Paragraph(item['item'], cell_style),
                        Paragraph(item['procedure'], cell_style),
                        Paragraph('✔' if checkbox_state and checkbox_state['checked'][0] else '', cell_style),
                        Paragraph('✔' if checkbox_state and checkbox_state['checked'][1] else '', cell_style),
                        Paragraph('✔' if checkbox_state and checkbox_state['checked'][2] else '', cell_style),
                        Paragraph(comment['text'], cell_style)
                    ])
                
                # Add total score row
                data.append([
                    Paragraph("", cell_style),
                    Paragraph("TOTAL SCORE", ParagraphStyle('Total', parent=cell_style, fontName='Helvetica-Bold')),
                    Paragraph("", cell_style),
                    Paragraph(str(eval1_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                    Paragraph(str(eval2_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                    Paragraph(str(eval3_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                    Paragraph("", cell_style)
                ])
                
                # Define column widths proportionally to the page width
                col_widths = [30, 140, 200, 35, 35, 35, 100]
                
                # Create table
                table = Table(data, colWidths=col_widths, repeatRows=1)
                
                # Style the table
                green_color = colors.Color(0.176, 0.416, 0.31)  # #2d6a4f in RGB
                light_green = colors.Color(0.925, 0.965, 0.945)  # Very light green for alternating rows
                
                table_style = TableStyle([
                    # Header row styling
                    ('BACKGROUND', (0, 0), (-1, 0), green_color),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    
                    # Alternating row colors
                    *[('BACKGROUND', (0, i), (-1, i), light_green) for i in range(2, len(data)-1, 2)],
                    
                    # Total row styling
                    ('BACKGROUND', (0, -1), (-1, -1), colors.white),
                    ('SPAN', (0, -1), (2, -1)),  # Span TOTAL SCORE across first three columns
                    
                    # Align checkmarks and scores to center
                    ('ALIGN', (3, 1), (5, -1), 'CENTER'),
                    ('FONTNAME', (3, 1), (5, -1), 'Helvetica-Bold'),  # Make checkmarks bold
                    ('FONTSIZE', (3, 1), (5, -1), 12),  # Increase checkmark size
                    
                    # Borders
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('BOX', (0, 0), (-1, -1), 2, colors.black),
                    
                    # Cell padding
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ])
                
                # Apply the style
                table.setStyle(table_style)
                elements.append(table)
                
                # Add signature lines
                elements.append(Spacer(1, 50))
                signature_data = [
                    ['________________________', '________________________'],
                    ['Parent/Guardian Signature', 'Date']
                ]
                signature_table = Table(signature_data, colWidths=[200, 200])
                signature_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, 1), 10),
                    ('TOPPADDING', (0, 1), (-1, 1), 5),
                ]))
                elements.append(signature_table)
                
                # Build PDF
                doc.build(elements)
                
                # Get PDF value from buffer
                pdf_value = buffer.getvalue()
                buffer.close()
                
                # Generate unique filename
                filename = f"parent_self_help_{student_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                # Save to SelfHelpPDF model
                pdf_record = SelfHelpPDF(
                    student_name=student_name,
                    eval1_score=eval1_score,
                    eval2_score=eval2_score,
                    eval3_score=eval3_score
                )
                pdf_record.file.save(filename, ContentFile(pdf_value), save=True)
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Evaluation saved and PDF generated successfully',
                    'evaluation_id': evaluation.id,
                    'pdf_url': pdf_record.file.url
                })
                
            except Exception as e:
                # Log PDF generation error but don't fail the whole request
                print(f"Error generating PDF: {str(e)}")
                return JsonResponse({
                    'status': 'partial_success',
                    'message': 'Evaluation saved but PDF generation failed',
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
            
            # Get checkbox states
            checkbox_data = []
            for i in range(1, 4):  # 3 evaluation items for gross motor
                eval1 = request.POST.get(f'checkbox_{i}_eval1') == '1'
                eval2 = request.POST.get(f'checkbox_{i}_eval2') == '1'
                eval3 = request.POST.get(f'checkbox_{i}_eval3') == '1'
                checkbox_data.append({
                    'number': i,
                    'checked': [eval1, eval2, eval3]
                })
            
            # Get comments if any
            comments = []
            for i in range(1, 4):  # 3 evaluation items
                comment = request.POST.get(f'comment_{i}', '')
                if comment:
                    comments.append({'number': i, 'text': comment})
            
            # Create a new evaluation record
            evaluation = ParentGrossEvaluation(
                student_name=student_name,
                eval1_score=eval1_score,
                eval2_score=eval2_score,
                eval3_score=eval3_score
            )
            evaluation.save()
            
            # Generate PDF
            try:
                # Create BytesIO buffer for PDF
                buffer = BytesIO()
                
                # Create the PDF object using reportlab
                doc = SimpleDocTemplate(
                    buffer,
                    pagesize=landscape(letter),
                    topMargin=30,
                    leftMargin=30,
                    rightMargin=30,
                    bottomMargin=30
                )
                
                # Define styles
                styles = getSampleStyleSheet()
                title_style = ParagraphStyle(
                    'Title',
                    parent=styles['Heading1'],
                    fontSize=18,
                    textColor=colors.darkgreen,
                    alignment=1,
                    spaceAfter=10
                )
                subtitle_style = ParagraphStyle(
                    'Subtitle',
                    parent=styles['Heading2'],
                    fontSize=14,
                    textColor=colors.darkgreen,
                    alignment=1,
                    spaceAfter=6
                )
                normal_style = ParagraphStyle(
                    'Normal',
                    parent=styles['Normal'],
                    fontSize=11,
                    leading=14,
                    spaceBefore=6,
                    spaceAfter=6
                )
                header_style = ParagraphStyle(
                    'TableHeader',
                    parent=styles['Normal'],
                    fontSize=11,
                    textColor=colors.white,
                    alignment=1,
                    fontName='Helvetica-Bold'
                )
                cell_style = ParagraphStyle(
                    'TableCell',
                    parent=styles['Normal'],
                    fontSize=10,
                    leading=14,
                    wordWrap='CJK'
                )
                
                # Create elements list for PDF content
                elements = []
                
                # Add title
                elements.append(Paragraph("Parent Gross Motor Evaluation", title_style))
                elements.append(Spacer(1, 5))
                elements.append(Paragraph(f"Student: {student_name}", subtitle_style))
                elements.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", normal_style))
                elements.append(Spacer(1, 15))
                
                # Create table data
                data = [
                    [
                        Paragraph("No.", header_style),
                        Paragraph("Gross Motor", header_style),
                        Paragraph("Material/Procedure", header_style),
                        Paragraph("1st Eval", header_style),
                        Paragraph("2nd Eval", header_style),
                        Paragraph("3rd Eval", header_style),
                        Paragraph("Comments", header_style)
                    ]
                ]
                
                # Define evaluation items
                evaluation_items = [
                    {
                        'number': '1',
                        'item': 'Climbs on the chair or other elevated furniture like a bed without a help',
                        'procedure': 'Parental report will suffice.'
                    },
                    {
                        'number': '2',
                        'item': 'Walks downstairs, 2 feet on each step, with one handheld',
                        'procedure': 'MATERIAL: toy<br/>PROCEDURE:<br/>Ask the child to walk backwards by demonstrating this. Credit if the child is able to walk backwards without falling and holding anything. Parental report will suffice.'
                    },
                    {
                        'number': '3',
                        'item': 'Dances patterns/joins group movement activities',
                        'procedure': 'MATERIAL: ball<br/>PROCEDURE:<br/>Encourage the child to run by rolling a ball across the floor. Credit if the child can run past and without tripping or falling.'
                    }
                ]
                
                # Add rows for each evaluation item
                for item in evaluation_items:
                    item_num = int(item['number'])
                    checkbox_state = next((x for x in checkbox_data if x['number'] == item_num), None)
                    comment = next((x for x in comments if x['number'] == item_num), {'text': ''})
                    
                    data.append([
                        Paragraph(item['number'], cell_style),
                        Paragraph(item['item'], cell_style),
                        Paragraph(item['procedure'], cell_style),
                        Paragraph('✓' if checkbox_state and checkbox_state['checked'][0] else '', cell_style),
                        Paragraph('✓' if checkbox_state and checkbox_state['checked'][1] else '', cell_style),
                        Paragraph('✓' if checkbox_state and checkbox_state['checked'][2] else '', cell_style),
                        Paragraph(comment['text'], cell_style)
                    ])
                
                # Add total score row
                data.append([
                    Paragraph("", cell_style),
                    Paragraph("TOTAL SCORE", ParagraphStyle('Total', parent=cell_style, fontName='Helvetica-Bold')),
                    Paragraph("", cell_style),
                    Paragraph(str(eval1_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                    Paragraph(str(eval2_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                    Paragraph(str(eval3_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                    Paragraph("", cell_style)
                ])
                
                # Define column widths proportionally to the page width
                col_widths = [40, 150, 200, 50, 50, 50, 100]
                
                # Create table
                table = Table(data, colWidths=col_widths)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
                    ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, -1), (-1, -1), 10),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)
                
                # Add signature lines
                elements.append(Spacer(1, 50))
                signature_data = [
                    ['________________________', '________________________'],
                    ['Parent/Guardian Signature', 'Date']
                ]
                signature_table = Table(signature_data, colWidths=[200, 200])
                signature_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, 1), 10),
                    ('TOPPADDING', (0, 1), (-1, 1), 5),
                ]))
                elements.append(signature_table)
                
                # Build PDF
                doc.build(elements)
                
                # Get PDF value from buffer
                pdf_value = buffer.getvalue()
                buffer.close()
                
                # Generate unique filename
                filename = f"parent_gross_motor_{student_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                # Save to GrossMotorPDF model
                pdf_record = GrossMotorPDF(
                    student_name=student_name,
                    eval1_score=eval1_score,
                    eval2_score=eval2_score,
                    eval3_score=eval3_score
                )
                pdf_record.file.save(filename, ContentFile(pdf_value), save=True)
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Evaluation saved and PDF generated successfully',
                    'evaluation_id': evaluation.id,
                    'pdf_url': pdf_record.file.url
                })
                
            except Exception as e:
                # Log PDF generation error but don't fail the whole request
                print(f"Error generating PDF: {str(e)}")
                return JsonResponse({
                    'status': 'partial_success',
                    'message': 'Evaluation saved but PDF generation failed',
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
    If method is POST, processes the submission and generates PDF.
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
            
            # Get checkbox states
            checkbox_data = []
            for i in range(1, 11):  # 10 evaluation items
                eval1 = request.POST.get(f'checkbox_{i}_eval1') == '1'
                eval2 = request.POST.get(f'checkbox_{i}_eval2') == '1'
                eval3 = request.POST.get(f'checkbox_{i}_eval3') == '1'
                checkbox_data.append({
                    'number': i,
                    'checked': [eval1, eval2, eval3]
                })
            
            # Get comments if any
            comments = []
            for i in range(1, 11):  # 10 evaluation items
                comment = request.POST.get(f'comment_{i}', '')
                if comment:
                    comments.append({'number': i, 'text': comment})
            
            # Create a new evaluation record
            evaluation = ParentSocialEvaluation(
                student_name=student_name,
                eval1_score=eval1_score,
                eval2_score=eval2_score,
                eval3_score=eval3_score
            )
            evaluation.save()
            
            # Generate PDF
            try:
                # Create BytesIO buffer for PDF
                buffer = BytesIO()
                
                # Create the PDF object using reportlab
                doc = SimpleDocTemplate(
                    buffer,
                    pagesize=landscape(letter),
                    topMargin=20,
                    leftMargin=20,
                    rightMargin=20,
                    bottomMargin=20
                )
                
                # Define styles
                styles = getSampleStyleSheet()
                title_style = ParagraphStyle(
                    'Title',
                    parent=styles['Heading1'],
                    fontSize=16,
                    textColor=colors.darkgreen,
                    alignment=1,
                    spaceAfter=8
                )
                subtitle_style = ParagraphStyle(
                    'Subtitle',
                    parent=styles['Heading2'],
                    fontSize=12,
                    textColor=colors.darkgreen,
                    alignment=1,
                    spaceAfter=4
                )
                normal_style = ParagraphStyle(
                    'Normal',
                    parent=styles['Normal'],
                    fontSize=10,
                    leading=12,
                    spaceBefore=4,
                    spaceAfter=4
                )
                header_style = ParagraphStyle(
                    'TableHeader',
                    parent=styles['Normal'],
                    fontSize=10,
                    textColor=colors.white,
                    alignment=1,
                    fontName='Helvetica-Bold'
                )
                cell_style = ParagraphStyle(
                    'TableCell',
                    parent=styles['Normal'],
                    fontSize=9,
                    leading=11,
                    wordWrap='CJK'
                )
                
                # Create elements list for PDF content
                elements = []
                
                # Add title
                elements.append(Paragraph("Parent Social-Emotional Evaluation", title_style))
                elements.append(Spacer(1, 5))
                elements.append(Paragraph(f"Student: {student_name}", subtitle_style))
                elements.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", normal_style))
                elements.append(Spacer(1, 10))
                
                # Define evaluation items
                evaluation_items = [
                    {
                        'number': '1',
                        'item': 'Responds to adult activities or nearby children',
                        'procedure': 'Parental report will suffice.'
                    },
                    {
                        'number': '2',
                        'item': 'Begins to recognize differences in emotions',
                        'procedure': 'Parental report will suffice.'
                    },
                    {
                        'number': '3',
                        'item': 'Plays alone but likes to be near adults or brothers and sisters',
                        'procedure': 'Parental report will suffice.'
                    },
                    {
                        'number': '4',
                        'item': 'Laughs or squeals about happy things',
                        'procedure': 'Parental report will suffice.'
                    },
                    {
                        'number': '5',
                        'item': 'Uses speech-like babbling',
                        'procedure': 'Parental report will suffice.'
                    },
                    {
                        'number': '6',
                        'item': 'Gets and interpretively into a sequence correctly',
                        'procedure': 'Parental report will suffice.'
                    },
                    {
                        'number': '7',
                        'item': 'Hugs or cuddles toys, companions, parents',
                        'procedure': 'Parental report will suffice.'
                    },
                    {
                        'number': '8',
                        'item': 'Demonstrates respect for others\' belongings and space',
                        'procedure': 'Parental report will suffice.'
                    },
                    {
                        'number': '9',
                        'item': 'Shows with pictures "sad" and "happy"',
                        'procedure': 'Parental report will suffice.'
                    },
                    {
                        'number': '10',
                        'item': 'Shares toys with others (e.g., cooking, pababa)',
                        'procedure': 'Parental report will suffice.'
                    }
                ]
                
                # Create table data
                data = [
                    [
                        Paragraph("No.", header_style),
                        Paragraph("Social-Emotional", header_style),
                        Paragraph("Material/Procedure", header_style),
                        Paragraph("1st", header_style),
                        Paragraph("2nd", header_style),
                        Paragraph("3rd", header_style),
                        Paragraph("Comments", header_style)
                    ]
                ]
                
                # Add rows for each evaluation item
                for item in evaluation_items:
                    item_num = int(item['number'])
                    checkbox_state = next((x for x in checkbox_data if x['number'] == item_num), None)
                    comment = next((x for x in comments if x['number'] == item_num), {'text': ''})
                    
                    data.append([
                        Paragraph(item['number'], cell_style),
                        Paragraph(item['item'], cell_style),
                        Paragraph(item['procedure'], cell_style),
                        Paragraph('✔' if checkbox_state and checkbox_state['checked'][0] else '', cell_style),
                        Paragraph('✔' if checkbox_state and checkbox_state['checked'][1] else '', cell_style),
                        Paragraph('✔' if checkbox_state and checkbox_state['checked'][2] else '', cell_style),
                        Paragraph(comment['text'], cell_style)
                    ])
                
                # Add total score row
                data.append([
                    Paragraph("", cell_style),
                    Paragraph("TOTAL SCORE", ParagraphStyle('Total', parent=cell_style, fontName='Helvetica-Bold')),
                    Paragraph("", cell_style),
                    Paragraph(str(eval1_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                    Paragraph(str(eval2_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                    Paragraph(str(eval3_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                    Paragraph("", cell_style)
                ])
                
                # Define column widths proportionally to the page width
                col_widths = [30, 140, 200, 35, 35, 35, 100]
                
                # Create table
                table = Table(data, colWidths=col_widths, repeatRows=1)
                
                # Style the table
                green_color = colors.Color(0.176, 0.416, 0.31)  # #2d6a4f in RGB
                light_green = colors.Color(0.925, 0.965, 0.945)  # Very light green for alternating rows
                
                table_style = TableStyle([
                    # Header row styling
                    ('BACKGROUND', (0, 0), (-1, 0), green_color),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    
                    # Alternating row colors
                    *[('BACKGROUND', (0, i), (-1, i), light_green) for i in range(2, len(data)-1, 2)],
                    
                    # Total row styling
                    ('BACKGROUND', (0, -1), (-1, -1), colors.white),
                    ('SPAN', (0, -1), (2, -1)),  # Span TOTAL SCORE across first three columns
                    
                    # Align checkmarks and scores to center
                    ('ALIGN', (3, 1), (5, -1), 'CENTER'),
                    ('FONTNAME', (3, 1), (5, -1), 'Helvetica-Bold'),  # Make checkmarks bold
                    ('FONTSIZE', (3, 1), (5, -1), 12),  # Increase checkmark size
                    
                    # Borders
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('BOX', (0, 0), (-1, -1), 2, colors.black),
                    
                    # Cell padding
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ])
                
                # Apply the style
                table.setStyle(table_style)
                elements.append(table)
                
                # Add signature line
                elements.append(Spacer(1, 30))
                signature_data = [
                    ['________________________', '________________________'],
                    ['Parent/Guardian Signature', 'Date']
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
                
                # Build PDF
                doc.build(elements)
                
                # Get PDF value from buffer
                pdf_value = buffer.getvalue()
                buffer.close()
                
                # Generate unique filename
                filename = f"parent_social_{student_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                # Save to SocialPDF model
                pdf_record = SocialPDF(
                    student_name=student_name,
                    eval1_score=eval1_score,
                    eval2_score=eval2_score,
                    eval3_score=eval3_score
                )
                pdf_record.file.save(filename, ContentFile(pdf_value), save=True)
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Evaluation saved and PDF generated successfully',
                    'evaluation_id': evaluation.id,
                    'pdf_url': pdf_record.file.url
                })
                
            except Exception as e:
                # Log PDF generation error but don't fail the whole request
                print(f"Error generating PDF: {str(e)}")
                return JsonResponse({
                    'status': 'partial_success',
                    'message': 'Evaluation saved but PDF generation failed',
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
    If method is POST, processes the submission and generates PDF.
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
            
            # Get checkbox states
            checkbox_data = []
            for i in range(1, 6):  # 5 evaluation items for expressive language
                eval1 = request.POST.get(f'checkbox_{i}_eval1') == '1'
                eval2 = request.POST.get(f'checkbox_{i}_eval2') == '1'
                eval3 = request.POST.get(f'checkbox_{i}_eval3') == '1'
                checkbox_data.append({
                    'number': i,
                    'checked': [eval1, eval2, eval3]
                })
            
            # Get comments if any
            comments = []
            for i in range(1, 6):  # 5 evaluation items
                comment = request.POST.get(f'comment_{i}', '')
                if comment:
                    comments.append({'number': i, 'text': comment})
            
            # Create a new evaluation record
            evaluation = ParentExpressiveEvaluation(
                student_name=student_name,
                eval1_score=eval1_score,
                eval2_score=eval2_score,
                eval3_score=eval3_score
            )
            evaluation.save()
            
            # Generate PDF
            try:
                # Create BytesIO buffer for PDF
                buffer = BytesIO()
                
                # Create the PDF object using reportlab
                doc = SimpleDocTemplate(
                    buffer,
                    pagesize=landscape(letter),
                    topMargin=20,
                    leftMargin=20,
                    rightMargin=20,
                    bottomMargin=20
                )
                
                # Define styles
                styles = getSampleStyleSheet()
                title_style = ParagraphStyle(
                    'Title',
                    parent=styles['Heading1'],
                    fontSize=16,
                    textColor=colors.darkgreen,
                    alignment=1,
                    spaceAfter=8
                )
                subtitle_style = ParagraphStyle(
                    'Subtitle',
                    parent=styles['Heading2'],
                    fontSize=12,
                    textColor=colors.darkgreen,
                    alignment=1,
                    spaceAfter=4
                )
                normal_style = ParagraphStyle(
                    'Normal',
                    parent=styles['Normal'],
                    fontSize=10,
                    leading=12,
                    spaceBefore=4,
                    spaceAfter=4
                )
                header_style = ParagraphStyle(
                    'TableHeader',
                    parent=styles['Normal'],
                    fontSize=10,
                    textColor=colors.white,
                    alignment=1,
                    fontName='Helvetica-Bold'
                )
                cell_style = ParagraphStyle(
                    'TableCell',
                    parent=styles['Normal'],
                    fontSize=9,
                    leading=11,
                    wordWrap='CJK'
                )
                
                # Create elements list for PDF content
                elements = []
                
                # Add title
                elements.append(Paragraph("Parent Expressive Language Evaluation", title_style))
                elements.append(Spacer(1, 5))
                elements.append(Paragraph(f"Student: {student_name}", subtitle_style))
                elements.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", normal_style))
                elements.append(Spacer(1, 10))
                
                # Create table data
                data = [
                    [
                        Paragraph("No.", header_style),
                        Paragraph("Expressive Language", header_style),
                        Paragraph("Material/Procedure", header_style),
                        Paragraph("1st", header_style),
                        Paragraph("2nd", header_style),
                        Paragraph("3rd", header_style),
                        Paragraph("Comments", header_style)
                    ]
                ]
                
                # Define evaluation items
                evaluation_items = [
                    {
                        'number': '1',
                        'item': 'Uses pronouns (e.g., I, me, ako, akin)',
                        'procedure': 'Parental report will suffice.'
                    },
                    {
                        'number': '2',
                        'item': 'Uses 2-to-3-word verb-noun combination (e.g., sipa patas)',
                        'procedure': 'Parental report will suffice.'
                    },
                    {
                        'number': '3',
                        'item': 'Speaks in grammatically correct 2- to 3-word sentences',
                        'procedure': 'Parental report will suffice.'
                    },
                    {
                        'number': '4',
                        'item': 'Ask "what" questions',
                        'procedure': 'Parental report will suffice.'
                    },
                    {
                        'number': '5',
                        'item': 'Ask "who" and "why" questions',
                        'procedure': 'Parental report will suffice.'
                    }
                ]
                
                # Add rows for each evaluation item
                for item in evaluation_items:
                    item_num = int(item['number'])
                    checkbox_state = next((x for x in checkbox_data if x['number'] == item_num), None)
                    comment = next((x for x in comments if x['number'] == item_num), {'text': ''})
                    
                    data.append([
                        Paragraph(item['number'], cell_style),
                        Paragraph(item['item'], cell_style),
                        Paragraph(item['procedure'], cell_style),
                        Paragraph('✔' if checkbox_state and checkbox_state['checked'][0] else '', cell_style),
                        Paragraph('✔' if checkbox_state and checkbox_state['checked'][1] else '', cell_style),
                        Paragraph('✔' if checkbox_state and checkbox_state['checked'][2] else '', cell_style),
                        Paragraph(comment['text'], cell_style)
                    ])
                
                # Add total score row
                data.append([
                    Paragraph("", cell_style),
                    Paragraph("TOTAL SCORE", ParagraphStyle('Total', parent=cell_style, fontName='Helvetica-Bold')),
                    Paragraph("", cell_style),
                    Paragraph(str(eval1_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                    Paragraph(str(eval2_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                    Paragraph(str(eval3_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                    Paragraph("", cell_style)
                ])
                
                # Define column widths proportionally to the page width
                col_widths = [30, 140, 200, 35, 35, 35, 100]
                
                # Create table
                table = Table(data, colWidths=col_widths, repeatRows=1)
                
                # Style the table
                green_color = colors.Color(0.176, 0.416, 0.31)  # #2d6a4f in RGB
                light_green = colors.Color(0.925, 0.965, 0.945)  # Very light green for alternating rows
                
                table_style = TableStyle([
                    # Header row styling
                    ('BACKGROUND', (0, 0), (-1, 0), green_color),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    
                    # Alternating row colors
                    *[('BACKGROUND', (0, i), (-1, i), light_green) for i in range(2, len(data)-1, 2)],
                    
                    # Total row styling
                    ('BACKGROUND', (0, -1), (-1, -1), colors.white),
                    ('SPAN', (0, -1), (2, -1)),  # Span TOTAL SCORE across first three columns
                    
                    # Align checkmarks and scores to center
                    ('ALIGN', (3, 1), (5, -1), 'CENTER'),
                    ('FONTNAME', (3, 1), (5, -1), 'Helvetica-Bold'),  # Make checkmarks bold
                    ('FONTSIZE', (3, 1), (5, -1), 12),  # Increase checkmark size
                    
                    # Borders
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('BOX', (0, 0), (-1, -1), 2, colors.black),
                    
                    # Cell padding
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ])
                
                # Apply the style
                table.setStyle(table_style)
                elements.append(table)
                
                # Add signature line
                elements.append(Spacer(1, 30))
                signature_data = [
                    ['________________________', '________________________'],
                    ['Parent/Guardian Signature', 'Date']
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
                
                # Build PDF
                doc.build(elements)
                
                # Get PDF value from buffer
                pdf_value = buffer.getvalue()
                buffer.close()
                
                # Generate unique filename
                filename = f"parent_expressive_{student_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                # Save to ExpressivePDF model
                pdf_record = ExpressivePDF(
                    student_name=student_name,
                    eval1_score=eval1_score,
                    eval2_score=eval2_score,
                    eval3_score=eval3_score
                )
                pdf_record.file.save(filename, ContentFile(pdf_value), save=True)
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Evaluation saved and PDF generated successfully',
                    'evaluation_id': evaluation.id,
                    'pdf_url': pdf_record.file.url
                })
                
            except Exception as e:
                # Log PDF generation error but don't fail the whole request
                print(f"Error generating PDF: {str(e)}")
                return JsonResponse({
                    'status': 'partial_success',
                    'message': 'Evaluation saved but PDF generation failed',
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
    If method is POST, processes the submission and generates PDF.
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
            
            # Get checkbox states
            checkbox_data = []
            for i in range(1, 6):  # 5 evaluation items
                eval1 = request.POST.get(f'checkbox_{i}_eval1') == '1'
                eval2 = request.POST.get(f'checkbox_{i}_eval2') == '1'
                eval3 = request.POST.get(f'checkbox_{i}_eval3') == '1'
                checkbox_data.append({
                    'number': i,
                    'checked': [eval1, eval2, eval3]
                })
            
            # Get comments if any
            comments = []
            for i in range(1, 6):  # 5 evaluation items
                comment = request.POST.get(f'comment_{i}', '')
                if comment:
                    comments.append({'number': i, 'text': comment})
            
            # Create a new evaluation record
            evaluation = ParentCognitiveEvaluation(
                student_name=student_name,
                eval1_score=eval1_score,
                eval2_score=eval2_score,
                eval3_score=eval3_score
            )
            evaluation.save()
            
            # Generate PDF
            try:
                # Create BytesIO buffer for PDF
                buffer = BytesIO()
                
                # Create the PDF object using reportlab
                doc = SimpleDocTemplate(
                    buffer,
                    pagesize=landscape(letter),
                    topMargin=20,
                    leftMargin=20,
                    rightMargin=20,
                    bottomMargin=20
                )
                
                # Define styles
                styles = getSampleStyleSheet()
                title_style = ParagraphStyle(
                    'Title',
                    parent=styles['Heading1'],
                    fontSize=16,
                    textColor=colors.darkgreen,
                    alignment=1,
                    spaceAfter=8
                )
                subtitle_style = ParagraphStyle(
                    'Subtitle',
                    parent=styles['Heading2'],
                    fontSize=12,
                    textColor=colors.darkgreen,
                    alignment=1,
                    spaceAfter=4
                )
                normal_style = ParagraphStyle(
                    'Normal',
                    parent=styles['Normal'],
                    fontSize=10,
                    leading=12,
                    spaceBefore=4,
                    spaceAfter=4
                )
                header_style = ParagraphStyle(
                    'TableHeader',
                    parent=styles['Normal'],
                    fontSize=10,
                    textColor=colors.white,
                    alignment=1,
                    fontName='Helvetica-Bold'
                )
                cell_style = ParagraphStyle(
                    'TableCell',
                    parent=styles['Normal'],
                    fontSize=9,
                    leading=11,
                    wordWrap='CJK'
                )
                
                # Create elements list for PDF content
                elements = []
                
                # Add title
                elements.append(Paragraph("Parent Cognitive Evaluation", title_style))
                elements.append(Spacer(1, 5))
                elements.append(Paragraph(f"Student: {student_name}", subtitle_style))
                elements.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", normal_style))
                elements.append(Spacer(1, 10))
                
                # Define evaluation items
                evaluation_items = [
                    {
                        'number': '1',
                        'item': 'Looks in the direction of fallen object',
                        'procedure': 'MATERIAL: spoon/ball<br/>PROCEDURE:<br/>With the child seated, get his attention and drop a spoon/ball in front of him. Then observe if his eyes look down as it falls.<br/>Credit if the child can bring his eyes and head down as the objects falls. Automatically credit if item 8.5 is passed.'
                    },
                    {
                        'number': '2',
                        'item': 'Looks for a partially hidden object',
                        'procedure': 'MATERIALS: spoon/ball<br/>PROCEDURE:<br/>With the child facing you, partially hide a ball behind a small towel and observe if he will look for it and find it. Credit if the child pulls the towel and gets the hidden ball. Automatically credit if item 8.5 is passed.'
                    },
                    {
                        'number': '3',
                        'item': 'Looks for a completely hidden object',
                        'procedure': 'MATERIALS: ball, small towel/cloth<br/>PROCEDURE:<br/>With the child facing you, hide a ball completely under a small towel and observe if he will look under the towel. Credit if he looks under the towel and gets the hidden ball.'
                    },
                    {
                        'number': '4',
                        'item': 'Exhibits simple "pretend" play (feeds, puts doll to sleep)',
                        'procedure': 'MATERIAL: doll or toy car/block<br/>PROCEDURE:<br/>If the child is a girl, carry the doll and pretend to rock it to sleep. If the child is a boy, move the car/block back and forth. Credit if the child can imitate this.'
                    },
                    {
                        'number': '5',
                        'item': 'Matches Objects',
                        'procedure': 'MATERIALS: pairs of spoons, ball, blocks<br/>PROCEDURE:<br/>Place 1 spoon, 1 ball and 1 block of the table. Give the child the other sets of objects arranged in random order. Demonstrate a matching response (e.g., spoon with spoon), then return the object to the child. Say, "Put each one on the one that is just like it." Credit if the child can match the objects correctly.'
                    }
                ]
                
                # Create table data
                data = [
                    [
                        Paragraph("No.", header_style),
                        Paragraph("Cognitive", header_style),
                        Paragraph("Material/Procedure", header_style),
                        Paragraph("1st", header_style),
                        Paragraph("2nd", header_style),
                        Paragraph("3rd", header_style),
                        Paragraph("Comments", header_style)
                    ]
                ]
                
                # Add rows for each evaluation item
                for item in evaluation_items:
                    item_num = int(item['number'])
                    checkbox_state = next((x for x in checkbox_data if x['number'] == item_num), None)
                    comment = next((x for x in comments if x['number'] == item_num), {'text': ''})
                    
                    data.append([
                        Paragraph(item['number'], cell_style),
                        Paragraph(item['item'], cell_style),
                        Paragraph(item['procedure'], cell_style),
                        Paragraph('✔' if checkbox_state and checkbox_state['checked'][0] else '', cell_style),
                        Paragraph('✔' if checkbox_state and checkbox_state['checked'][1] else '', cell_style),
                        Paragraph('✔' if checkbox_state and checkbox_state['checked'][2] else '', cell_style),
                        Paragraph(comment['text'], cell_style)
                    ])
                
                # Add total score row
                data.append([
                    Paragraph("", cell_style),
                    Paragraph("TOTAL SCORE", ParagraphStyle('Total', parent=cell_style, fontName='Helvetica-Bold')),
                    Paragraph("", cell_style),
                    Paragraph(str(eval1_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                    Paragraph(str(eval2_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                    Paragraph(str(eval3_score), ParagraphStyle('Total', parent=cell_style, alignment=1, fontName='Helvetica-Bold')),
                    Paragraph("", cell_style)
                ])
                
                # Define column widths proportionally to the page width
                col_widths = [30, 140, 200, 35, 35, 35, 100]
                
                # Create table
                table = Table(data, colWidths=col_widths, repeatRows=1)
                
                # Style the table
                green_color = colors.Color(0.176, 0.416, 0.31)  # #2d6a4f in RGB
                light_green = colors.Color(0.925, 0.965, 0.945)  # Very light green for alternating rows
                
                table_style = TableStyle([
                    # Header row styling
                    ('BACKGROUND', (0, 0), (-1, 0), green_color),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    
                    # Alternating row colors
                    *[('BACKGROUND', (0, i), (-1, i), light_green) for i in range(2, len(data)-1, 2)],
                    
                    # Total row styling
                    ('BACKGROUND', (0, -1), (-1, -1), colors.white),
                    ('SPAN', (0, -1), (2, -1)),  # Span TOTAL SCORE across first three columns
                    
                    # Align checkmarks and scores to center
                    ('ALIGN', (3, 1), (5, -1), 'CENTER'),
                    ('FONTNAME', (3, 1), (5, -1), 'Helvetica-Bold'),  # Make checkmarks bold
                    ('FONTSIZE', (3, 1), (5, -1), 12),  # Increase checkmark size
                    
                    # Borders
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('BOX', (0, 0), (-1, -1), 2, colors.black),
                    
                    # Cell padding
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ])
                
                # Apply the style
                table.setStyle(table_style)
                elements.append(table)
                
                # Add signature line
                elements.append(Spacer(1, 30))
                signature_data = [
                    ['________________________', '________________________'],
                    ['Parent/Guardian Signature', 'Date']
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
                
                # Build PDF
                doc.build(elements)
                
                # Get PDF value from buffer
                pdf_value = buffer.getvalue()
                buffer.close()
                
                # Generate unique filename
                filename = f"parent_cognitive_{student_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                # Save to CognitivePDF model
                pdf_record = CognitivePDF(
                    student_name=student_name,
                    eval1_score=eval1_score,
                    eval2_score=eval2_score,
                    eval3_score=eval3_score
                )
                pdf_record.file.save(filename, ContentFile(pdf_value), save=True)
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Evaluation saved and PDF generated successfully',
                    'evaluation_id': evaluation.id,
                    'pdf_url': pdf_record.file.url
                })
                
            except Exception as e:
                # Log PDF generation error but don't fail the whole request
                print(f"Error generating PDF: {str(e)}")
                return JsonResponse({
                    'status': 'partial_success',
                    'message': 'Evaluation saved but PDF generation failed',
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
def evaluation_reports(request):
    """
    View for displaying and searching evaluation reports.
    """
    student_name = request.GET.get('student_name', '')
    evaluation_type = request.GET.get('evaluation_type', '')
    
    # Initialize empty querysets
    pdfs = {
        'gross_motor': {
            'teacher': GrossMotorPDFTeacher.objects.none(),
            'parent': GrossMotorPDF.objects.none()
        },
        'fine_motor': FinePDFTeacher.objects.none(),
        'self_help': {
            'teacher': SelfHelpPDFTeacher.objects.none(),
            'parent': SelfHelpPDF.objects.none()
        },
        'cognitive': {
            'teacher': CognitivePDFTeacher.objects.none(),
            'parent': CognitivePDF.objects.none()
        },
        'expressive': {
            'teacher': ExpressivePDFTeacher.objects.none(),
            'parent': ExpressivePDF.objects.none()
        },
        'receptive': ReceptivePDFTeacher.objects.none(),
        'social': {
            'parent': SocialPDF.objects.none()
        }
    }
    
    if student_name:
        # Filter PDFs by student name
        pdfs = {
            'gross_motor': {
                'teacher': GrossMotorPDFTeacher.objects.filter(student_name__icontains=student_name).order_by('-uploaded_at'),
                'parent': GrossMotorPDF.objects.filter(student_name__icontains=student_name).order_by('-uploaded_at')
            },
            'fine_motor': FinePDFTeacher.objects.filter(student_name__icontains=student_name).order_by('-uploaded_at'),
            'self_help': {
                'teacher': SelfHelpPDFTeacher.objects.filter(student_name__icontains=student_name).order_by('-uploaded_at'),
                'parent': SelfHelpPDF.objects.filter(student_name__icontains=student_name).order_by('-uploaded_at')
            },
            'cognitive': {
                'teacher': CognitivePDFTeacher.objects.filter(student_name__icontains=student_name).order_by('-uploaded_at'),
                'parent': CognitivePDF.objects.filter(student_name__icontains=student_name).order_by('-uploaded_at')
            },
            'expressive': {
                'teacher': ExpressivePDFTeacher.objects.filter(student_name__icontains=student_name).order_by('-uploaded_at'),
                'parent': ExpressivePDF.objects.filter(student_name__icontains=student_name).order_by('-uploaded_at')
            },
            'receptive': ReceptivePDFTeacher.objects.filter(student_name__icontains=student_name).order_by('-uploaded_at'),
            'social': {
                'parent': SocialPDF.objects.filter(student_name__icontains=student_name).order_by('-uploaded_at')
            }
        }
        
        # If evaluation type is specified, only keep that type
        if evaluation_type and evaluation_type in pdfs:
            filtered_pdfs = {evaluation_type: pdfs[evaluation_type]}
            pdfs = filtered_pdfs
    
    context = {
        'pdfs': pdfs,
        'student_name': student_name,
        'evaluation_type': evaluation_type,
        'evaluation_types': [
            ('gross_motor', 'Gross Motor'),
            ('fine_motor', 'Fine Motor'),
            ('self_help', 'Self Help'),
            ('cognitive', 'Cognitive'),
            ('expressive', 'Expressive Language'),
            ('receptive', 'Receptive Language'),
            ('social', 'Social-Emotional')
        ]
    }
    
    return render(request, 'evaluation_reports.html', context)

@login_required
def teacher_evaluation_pdfs(request):
    """
    View for displaying teacher's evaluation PDFs for the logged-in user's associated student.
    """
    # Get the logged-in user's username
    username = request.user.username
    
    # Get student based on the username
    student = Student.objects.filter(username=username).first()
    
    if not student:
        # Handle case where student is not found
        context = {
            'error_message': 'No student record found for your account.'
        }
        return render(request, 'teacher_evaluation_pdfs.html', context)
    
    # Get the student's name
    student_name = student.child_name
    
    # Fetch all evaluation PDFs for this student
    pdfs = {
        'gross_motor': GrossMotorPDFTeacher.objects.filter(student_name__icontains=student_name).order_by('-uploaded_at'),
        'fine_motor': FinePDFTeacher.objects.filter(student_name__icontains=student_name).order_by('-uploaded_at'),
        'self_help': SelfHelpPDFTeacher.objects.filter(student_name__icontains=student_name).order_by('-uploaded_at'),
        'cognitive': CognitivePDFTeacher.objects.filter(student_name__icontains=student_name).order_by('-uploaded_at'),
        'expressive': ExpressivePDFTeacher.objects.filter(student_name__icontains=student_name).order_by('-uploaded_at'),
        'receptive': ReceptivePDFTeacher.objects.filter(student_name__icontains=student_name).order_by('-uploaded_at'),
    }
    
    # Only include categories that have at least one evaluation
    filtered_pdfs = {}
    for eval_type, reports in pdfs.items():
        if reports.exists():
            filtered_pdfs[eval_type] = reports
    
    context = {
        'pdfs': filtered_pdfs,
        'student_name': student_name,
        'evaluation_types': [
            ('gross_motor', 'Gross Motor'),
            ('fine_motor', 'Fine Motor'),
            ('self_help', 'Self Help'),
            ('cognitive', 'Cognitive'),
            ('expressive', 'Expressive Language'),
            ('receptive', 'Receptive Language'),
        ]
    }
    
    return render(request, 'teacher_evaluation_pdfs.html', context)
