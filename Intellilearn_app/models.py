from django.db import models

# --- USERS ---
class User(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    image = models.FileField(upload_to="images/", null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    phone = models.IntegerField(null=True, blank=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=30, null=True, blank=True)
    confirmpassword = models.CharField(max_length=30, null=True, blank=True)
    currenteducation = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return self.name

class TeacherReg(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    image = models.FileField(upload_to="images/", null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    phone = models.IntegerField(null=True, blank=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=30, null=True, blank=True)
    confirmpassword = models.CharField(max_length=30, null=True, blank=True)
    experience = models.CharField(max_length=255, null=True, blank=True)
    specialization = models.CharField(max_length=255, null=True, blank=True)
    isapproved = models.BooleanField(default=False)
    isrejected = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name

# --- CONTENT & LEARNING ---
class ContentLibrary(models.Model):
    teacher = models.ForeignKey(TeacherReg, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='teacher_uploads/')
    ai_summary = models.TextField(blank=True, null=True)
    ai_quiz = models.TextField(blank=True, null=True) # JSON String
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class CourseProgress(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.ForeignKey(ContentLibrary, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    progress_percent = models.IntegerField(default=0)
    last_accessed = models.DateTimeField(auto_now=True)

class QuizResult(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.ForeignKey(ContentLibrary, on_delete=models.CASCADE, null=True, blank=True)
    topic = models.CharField(max_length=200, null=True, blank=True) 
    score = models.IntegerField()
    total_questions = models.IntegerField()
    date_taken = models.DateTimeField(auto_now_add=True)
    # NEW FIELD: To store the user's answers history
    answers_json = models.TextField(default="{}") 

class StudentProfile(models.Model):
    student = models.OneToOneField(User, on_delete=models.CASCADE)
    total_learning_minutes = models.IntegerField(default=0)
    streak_days = models.IntegerField(default=1)
    # Set default to "Not Set" so we know if they haven't taken the test yet
    learning_style = models.CharField(max_length=50, default="Not Set") 

class Achievement(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    icon_class = models.CharField(max_length=50, default="fa-solid fa-trophy")

class StudentAchievement(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    date_earned = models.DateTimeField(auto_now_add=True)

class StudentEvent(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    day = models.CharField(max_length=10) 
    time_slot = models.CharField(max_length=10) 
    location = models.CharField(max_length=50, blank=True, default="Classroom")
    color = models.CharField(max_length=20, default="evt-blue")

    class Meta:
        unique_together = ('student', 'day', 'time_slot')

    def __str__(self):
        return f"{self.subject} ({self.day} @ {self.time_slot})"

# --- NEW MODEL FOR CLASS MANAGEMENT ---
class Classroom(models.Model):
    teacher = models.ForeignKey(TeacherReg, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)   # e.g., CS101
    subject = models.CharField(max_length=100) # e.g., Intro to Python
    students = models.ManyToManyField(User, related_name='enrolled_classes', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.teacher.name}"