from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import random
import string
from django.db.models import Sum

class Student(models.Model):
    child_name = models.CharField(max_length=255)
    sex = models.CharField(max_length=10)
    dob = models.DateField()
    address = models.CharField(max_length=255)
    barangay = models.CharField(max_length=255)
    municipality = models.CharField(max_length=255)
    province = models.CharField(max_length=255)
    region = models.CharField(max_length=255)
    handedness = models.CharField(max_length=50)
    studying = models.CharField(max_length=10)
    father_name = models.CharField(max_length=255)
    father_age = models.IntegerField()
    father_occupation = models.CharField(max_length=255)
    father_education = models.CharField(max_length=255)
    mother_name = models.CharField(max_length=255)
    mother_age = models.IntegerField()
    mother_occupation = models.CharField(max_length=255)
    mother_education = models.CharField(max_length=255)
    num_siblings = models.IntegerField()
    birth_order = models.CharField(max_length=50)
    gmail = models.CharField(max_length=100, unique=True, null=True, blank=True)
    username = models.CharField(max_length=255, null=True, blank=True)
    session_no = models.IntegerField(default=1)

    
    
    def __str__(self):
        return self.child_name

    def get_highest_score(self):
        """Get the highest score across all evaluations for sorting"""
        scores = self.get_total_evaluation_score()
        return max(
            scores['eval1_total'],
            scores['eval2_total'],
            scores['eval3_total']
        )

    def get_total_evaluation_score(self):
        """Calculate total evaluation scores for each evaluation period"""
        from django.db.models import Sum
        
        # Get all teacher evaluations
        teacher_evaluations = EvaluationDataTeacher.objects.filter(child_name=self.child_name)
        teacher_totals = teacher_evaluations.aggregate(
            eval1=Sum('first_eval_score'),
            eval2=Sum('second_eval_score'),
            eval3=Sum('third_eval_score')
        )
        
        # Get all parent evaluations
        parent_evaluations = EvaluationData.objects.filter(child_name=self.child_name)
        parent_totals = parent_evaluations.aggregate(
            eval1=Sum('first_eval_score'),
            eval2=Sum('second_eval_score'),
            eval3=Sum('third_eval_score')
        )

        # Add teacher and parent scores for each evaluation
        eval1_total = (teacher_totals['eval1'] or 0) + (parent_totals['eval1'] or 0)
        eval2_total = (teacher_totals['eval2'] or 0) + (parent_totals['eval2'] or 0)
        eval3_total = (teacher_totals['eval3'] or 0) + (parent_totals['eval3'] or 0)

        return {
            'eval1_total': eval1_total,
            'eval2_total': eval2_total,
            'eval3_total': eval3_total
        }

@receiver(post_save, sender=Student)
def create_user_for_student(sender, instance, created, **kwargs):
    if created and instance.gmail:
        # Create user based on the email field if not exists
        if not User.objects.filter(username=instance.gmail).exists():
            # Generate a random password that will be reset via email
            random_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            
            # Create user with email as username in Django's auth system
            user = User.objects.create_user(
                username=instance.gmail,
                email=instance.gmail,
                password=random_password
            )
            
            # Set the first_name to be the student's name for display purposes
            if instance.username:
                user.first_name = instance.username
                user.save()
            
            # TODO: Send email with login instructions and password reset link

class EvaluationRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    evaluation_date = models.DateField(auto_now_add=True)
    evaluation_number = models.IntegerField()  # 1, 2, or 3
    
    # Scores for each domain
    cognitive_score = models.IntegerField()
    fine_motor_score = models.IntegerField()
    gross_motor_score = models.IntegerField()
    self_help_score = models.IntegerField()
    social_emotional_score = models.IntegerField()
    expressive_language_score = models.IntegerField()
    receptive_language_score = models.IntegerField()

    class Meta:
        unique_together = ['student', 'evaluation_number']






 #teacher's evaluation



#parent's evaluation
        

class PDFFile(models.Model):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='pdfs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    size = models.PositiveIntegerField()  # File size in bytes
    
    @property
    def size_display(self):
        """Convert size in bytes to human-readable format"""
        size = self.size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024 or unit == 'GB':
                return f"{size:.2f} {unit}"
            size /= 1024
    
    def __str__(self):
        return self.name

class Announcement(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class Event(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    color = models.CharField(max_length=20, default='#2d6a4f')  # Default to primary color

    class Meta:
        ordering = ['start_date']

    def __str__(self):
        return self.title

class EvaluationForm(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class EvaluationRow(models.Model):
    form = models.ForeignKey(EvaluationForm, on_delete=models.CASCADE, related_name='rows')
    name = models.CharField(max_length=255)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.form.name} - {self.name}"

class EvaluationColumn(models.Model):
    COLUMN_TYPES = [
        ('text', 'Text'),
        ('checkbox', 'Checkbox'),
    ]
    
    row = models.ForeignKey(EvaluationRow, on_delete=models.CASCADE, related_name='columns')
    name = models.CharField(max_length=255)
    column_type = models.CharField(max_length=20, choices=COLUMN_TYPES, default='text')
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.row.name} - {self.name} ({self.column_type})"

class EditableEvaluationTable(models.Model):
    EVALUATOR_CHOICES = [
        ('TEACHER', 'Teacher'),
        ('PARENT', 'Parent'),
    ]
    
    name = models.CharField(max_length=255)
    evaluator_type = models.CharField(
        max_length=10,
        choices=EVALUATOR_CHOICES,
        default='TEACHER',
        null=False,
        blank=False
    )
    data = models.JSONField() # Stores the full table as JSON
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.evaluator_type})"

class EvaluationData(models.Model):
    EVALUATOR_CHOICES = [
        ('TEACHER', 'Teacher'),
        ('PARENT', 'Parent'),
    ]
    
    EVALUATION_TYPES = [
        ('GROSS_MOTOR', 'Gross Motor'),
        ('FINE_MOTOR', 'Fine Motor'),
        ('SELF_HELP', 'Self Help'),
        ('COGNITIVE', 'Cognitive'),
        ('EXPRESSIVE', 'Expressive Language'),
        ('RECEPTIVE', 'Receptive Language'),
        ('SOCIAL', 'Social-Emotional'),
    ]

    child_name = models.CharField(max_length=255)
    evaluation_type = models.CharField(max_length=50, choices=EVALUATION_TYPES)
    evaluator_type = models.CharField(max_length=10, choices=EVALUATOR_CHOICES)
    first_eval_score = models.IntegerField()
    second_eval_score = models.IntegerField()
    third_eval_score = models.IntegerField()
    data = models.JSONField(null=True, blank=True)  # For storing additional form data
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['child_name', 'evaluation_type', 'evaluator_type']

    def __str__(self):
        return f"{self.child_name} - {self.evaluation_type} ({self.evaluator_type})"
    
class EvaluationDataTeacher(models.Model):
    EVALUATOR_CHOICES = [
        ('TEACHER', 'Teacher'),
        ('PARENT', 'Parent'),
    ]
    
    EVALUATION_TYPES = [
        ('GROSS_MOTOR', 'Gross Motor'),
        ('FINE_MOTOR', 'Fine Motor'),
        ('SELF_HELP', 'Self Help'),
        ('COGNITIVE', 'Cognitive'),
        ('EXPRESSIVE', 'Expressive Language'),
        ('RECEPTIVE', 'Receptive Language'),
        ('SOCIAL', 'Social-Emotional'),
    ]

    child_name = models.CharField(max_length=255)
    evaluation_type = models.CharField(max_length=50, choices=EVALUATION_TYPES)
    evaluator_type = models.CharField(max_length=10, choices=EVALUATOR_CHOICES)
    first_eval_score = models.IntegerField()
    second_eval_score = models.IntegerField()
    third_eval_score = models.IntegerField()
    data = models.JSONField(null=True, blank=True)  # For storing additional form data
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['child_name', 'evaluation_type', 'evaluator_type']

    def __str__(self):
        return f"{self.child_name} - {self.evaluation_type} ({self.evaluator_type})"
    

