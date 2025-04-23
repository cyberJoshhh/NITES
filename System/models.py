from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

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
    username = models.CharField(max_length=100, unique=True, null=True, blank=True)
    password = models.CharField(max_length=128, null=True, blank=True)
    session_no = models.IntegerField(default=1)
    
    
    def __str__(self):
        return self.child_name

@receiver(post_save, sender=Student)
def create_user_for_student(sender, instance, created, **kwargs):
    if created:
        # Create user based on the username and password fields
        if not User.objects.filter(username=instance.username).exists():
            User.objects.create_user(
                username=instance.username,
                password=instance.password
            )

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
class CognitiveEvaluation(models.Model):
    student_name = models.CharField(max_length=255)
    eval1_score = models.IntegerField()
    eval2_score = models.IntegerField()
    eval3_score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_name} - {self.created_at}"
    
class ExpressiveEvaluation(models.Model):
    student_name = models.CharField(max_length=255)
    eval1_score = models.IntegerField()
    eval2_score = models.IntegerField()
    eval3_score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_name} - {self.created_at}"
    
class FineEvaluation(models.Model):
    student_name = models.CharField(max_length=255)
    eval1_score = models.IntegerField()
    eval2_score = models.IntegerField()
    eval3_score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_name} - {self.created_at}"

class GrossEvaluation(models.Model):
    student_name = models.CharField(max_length=255)
    eval1_score = models.IntegerField()
    eval2_score = models.IntegerField()
    eval3_score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_name} - {self.created_at}"
    
class ReceptiveEvaluation(models.Model):
    student_name = models.CharField(max_length=255)
    eval1_score = models.IntegerField()
    eval2_score = models.IntegerField()
    eval3_score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_name} - {self.created_at}"
    
class SelfHelpEvaluation(models.Model):
    student_name = models.CharField(max_length=255)
    eval1_score = models.IntegerField()
    eval2_score = models.IntegerField()
    eval3_score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_name} - {self.created_at}"

class SocialEvaluation(models.Model):
    student_name = models.CharField(max_length=255)
    eval1_score = models.IntegerField()
    eval2_score = models.IntegerField()
    eval3_score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_name} - {self.created_at}"


#parent's evaluation
class ParentSocialEvaluation(models.Model):
    student_name = models.CharField(max_length=255)
    eval1_score = models.IntegerField()
    eval2_score = models.IntegerField()
    eval3_score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_name} - {self.created_at}"

class ParentSelfHelpEvaluation(models.Model):
    student_name = models.CharField(max_length=255)
    eval1_score = models.IntegerField()
    eval2_score = models.IntegerField()
    eval3_score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_name} - {self.created_at}"

class ParentGrossEvaluation(models.Model):
    student_name = models.CharField(max_length=255)
    eval1_score = models.IntegerField()
    eval2_score = models.IntegerField()
    eval3_score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_name} - {self.created_at}"

class ParentCognitiveEvaluation(models.Model):
    student_name = models.CharField(max_length=255)
    eval1_score = models.IntegerField()
    eval2_score = models.IntegerField()
    eval3_score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_name} - {self.created_at}"

class ParentExpressiveEvaluation(models.Model):
    student_name = models.CharField(max_length=255)
    eval1_score = models.IntegerField()
    eval2_score = models.IntegerField()
    eval3_score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_name} - {self.created_at}"
        
class TotalScores(models.Model):
    student_name = models.CharField(max_length=255)
    eval1_total = models.IntegerField()
    eval2_total = models.IntegerField()
    eval3_total = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student_name} - {self.created_at}"

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

class EvaluationPDF(models.Model):
    """
    Model to link evaluation records with their generated PDF files.
    This model helps track which evaluations have associated PDF documents.
    """
    student_name = models.CharField(max_length=255)
    evaluation_type = models.CharField(max_length=50, choices=[
        ('gross_motor', 'Gross Motor'),
        ('fine_motor', 'Fine Motor'),
        ('self_help', 'Self Help'),
        ('cognitive', 'Cognitive'),
        ('expressive', 'Expressive Language'),
        ('receptive', 'Receptive Language'),
        ('social', 'Social-Emotional')
    ])
    pdf_file = models.ForeignKey(PDFFile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.evaluation_type} - {self.student_name} - {self.created_at.strftime('%Y-%m-%d')}"

class GrossMotorPDF(models.Model):
    """
    Dedicated model to store Gross Motor PDF files directly.
    This is a standalone model that doesn't require linking to PDFFile.
    """
    student_name = models.CharField(max_length=255)
    file = models.FileField(upload_to='gross_motor_pdfs/')
    eval1_score = models.IntegerField()
    eval2_score = models.IntegerField()
    eval3_score = models.IntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Gross Motor PDF - {self.student_name} - {self.uploaded_at.strftime('%Y-%m-%d')}"

class SelfHelpPDF(models.Model):
    """
    Dedicated model to store Self-Help PDF files directly.
    This is a standalone model that doesn't require linking to PDFFile.
    """
    student_name = models.CharField(max_length=255)
    file = models.FileField(upload_to='self_help_pdfs/')
    eval1_score = models.IntegerField()
    eval2_score = models.IntegerField()
    eval3_score = models.IntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Self-Help PDF - {self.student_name} - {self.uploaded_at.strftime('%Y-%m-%d')}"

class SocialPDF(models.Model):
    """
    Dedicated model to store Social-Emotional PDF files directly.
    This is a standalone model that doesn't require linking to PDFFile.
    """
    student_name = models.CharField(max_length=255)
    file = models.FileField(upload_to='social_pdfs/')
    eval1_score = models.IntegerField()
    eval2_score = models.IntegerField()
    eval3_score = models.IntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Social-Emotional PDF - {self.student_name} - {self.uploaded_at.strftime('%Y-%m-%d')}"

class ExpressivePDF(models.Model):
    """
    Dedicated model to store Expressive Language PDF files directly.
    This is a standalone model that doesn't require linking to PDFFile.
    """
    student_name = models.CharField(max_length=255)
    file = models.FileField(upload_to='expressive_pdfs/')
    eval1_score = models.IntegerField()
    eval2_score = models.IntegerField()
    eval3_score = models.IntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Expressive Language PDF - {self.student_name} - {self.uploaded_at.strftime('%Y-%m-%d')}"

class CognitivePDF(models.Model):
    """
    Dedicated model to store Cognitive PDF files directly.
    This is a standalone model that doesn't require linking to PDFFile.
    """
    student_name = models.CharField(max_length=255)
    file = models.FileField(upload_to='cognitive_pdfs/')
    eval1_score = models.IntegerField()
    eval2_score = models.IntegerField()
    eval3_score = models.IntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Cognitive PDF - {self.student_name} - {self.uploaded_at.strftime('%Y-%m-%d')}"

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

