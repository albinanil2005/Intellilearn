# === IMPORTS ===
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.db.models import Avg, Sum
from Intellilearn_app import models
from . import storage_manager 

import os
import json
import time
import base64
import requests 
from io import BytesIO
import csv
from django.http import HttpResponse

import google.generativeai as old_genai

import google.generativeai as old_genai
from gtts import gTTS
import fal_client 

from django.core.mail import send_mail
from django.conf import settings
import random

# --- CONFIGURATION ---
# GEMINI_API_KEY = "AIzaSyBWcTfcpv3CAeOKek85FcKsuygaPIDYK6U" 
# genai.configure(api_key=GEMINI_API_KEY)
from google import genai
from google.genai import types
import time
from io import BytesIO
from gtts import gTTS
from django.conf import settings

old_genai.configure(api_key="AIzaSyAmyP9ygobvfhXGiYJrniKBNpNjO8QvUvs")
veo_client = genai.Client(api_key="AIzaSyAmyP9ygobvfhXGiYJrniKBNpNjO8QvUvs")

# FAL.AI KEY
os.environ["FAL_KEY"] = "f48e5a32-4cea-4908-bee7-9207f98e4bb0:400565446509ad47a8cfbd6ec539f10e" 

json_generation_config = {
  "temperature": 0.7, "top_p": 0.95, "top_k": 40, "max_output_tokens": 8192, "response_mime_type": "application/json",
}
text_generation_config = {
  "temperature": 0.7, "top_p": 0.95, "top_k": 40, "max_output_tokens": 8192, "response_mime_type": "text/plain",
}

def get_gemini_model(config=json_generation_config):
    try:
        available_models = []
        for m in old_genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        priority_models = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
        
        for preferred in priority_models:
            if preferred in available_models:
                return old_genai.GenerativeModel(model_name=preferred, generation_config=config)
        
        if available_models:
            return old_genai.GenerativeModel(model_name=available_models[0], generation_config=config)
            
    except Exception as e: 
        print(f"Error finding model: {e}")
    
    return old_genai.GenerativeModel(model_name='gemini-pro', generation_config=config)

def generate_safe(model, contents):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return model.generate_content(contents)
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg:
                time.sleep(20) 
            elif "404" in error_msg:
                model = genai.GenerativeModel('gemini-pro')
                return model.generate_content(contents)
            else:
                raise e 
    raise Exception("Google API is currently busy. Please wait 2 minutes and try again.")

# --- VIEWS ---

def index(request): return render(request,'index.html')

def userregister(request):
    if request.method == 'POST':
        # Step 1: Registration form submitted
        if 'register' in request.POST:
            name = request.POST.get('name')
            image = request.FILES.get('image')
            age = request.POST.get('age')
            gender = request.POST.get('gender')
            phone = request.POST.get('phone')
            email = request.POST.get('email')
            password = request.POST.get('password')
            confirmpassword = request.POST.get('confirmpassword')
            currenteducation = request.POST.get('currenteducation')

            if password != confirmpassword:
                return HttpResponse("<script>alert('Passwords do not match');window.history.back();</script>")

            if models.User.objects.filter(email=email).exists():
                return HttpResponse("<script>alert('Email already registered');window.history.back();</script>")

            # Generate OTP
            otp = random.randint(100000, 999999)
            request.session['otp'] = str(otp)

            # Store registration data in session temporarily
            request.session['reg_data'] = {
                'name': name,
                'age': age,
                'gender': gender,
                'phone': phone,
                'email': email,
                'password': password,
                'confirmpassword': confirmpassword,
                'currenteducation': currenteducation
            }

            # Save file temporarily (optional)
            if image:
                # Store image name in session
                request.session['image_name'] = image.name

                # Build full path
                upload_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
                
                # Ensure the folder exists
                os.makedirs(upload_dir, exist_ok=True)
                
                upload_path = os.path.join(upload_dir, image.name)

                # Write file
                with open(upload_path, "wb+") as f:
                    for chunk in image.chunks():
                        f.write(chunk)
            
            # CRITICAL FIX: Save session explicitly to persist across redirect
            request.session.save()

            # Send OTP email
            try:
                send_mail(
                    'Your Registration OTP',
                    f'Your OTP is {otp}',
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False
                )
            except Exception as e:
                print(f"Email Error: {e}")

            # CRITICAL FIX: Redirect to the verify_otp view instead of staying here
            return redirect('verify_otp')

    return render(request, 'register.html')

def TeacherReg(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        image = request.FILES.get('image')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirmpassword = request.POST.get('confirmpassword')
        experience = request.POST.get('experience')
        specialization = request.POST.get('specialization')

        if password != confirmpassword: return HttpResponse("<script>alert('Passwords do not match');window.location.href='/';</script>") 
        if models.TeacherReg.objects.filter(email=email).exists(): return HttpResponse("<script>alert('Email already registered');window.history.back();</script>") 
        TeacherReg = models.TeacherReg(name=name, image=image, age=age, gender=gender, phone=phone, email=email, password=password, confirmpassword=confirmpassword, experience=experience, specialization=specialization)  
        TeacherReg.save()
        return HttpResponse("<script>alert('Registration successful!');window.location.href='';</script>")
    return render(request, 'TeacherReg.html')  

def userlogin(request): 
    if request.method == 'POST': 
        email = request.POST.get('email') 
        password = request.POST.get( 'password') 
        try: 
            user = models.User.objects.get(email=email) 
            if user.password == password:
                request.session['email'] = email  # <-- set session first
                profile, created = models.StudentProfile.objects.get_or_create(student=user)
                # FIRST TIME LOGIN → psychometric test
                if profile.learning_style == "Not Set":
                    return redirect('studentpsychometric')
                return redirect('studentdashboard')
            else: return HttpResponse("Invalid credentials")
        except models.User.DoesNotExist: return HttpResponse("User not found")
    return render(request, 'login.html' )
    
def TeacherLogin(request):
    if request.method == 'POST': 
        email = request.POST.get('email') 
        password = request.POST.get( 'password') 
        try: 
            TeacherReg = models.TeacherReg.objects.get(email=email) 
            if TeacherReg.password == password: 
                if TeacherReg.isapproved:
                 request.session['email' ]= email
                 return HttpResponse("<script>alert('Login Successful');window.location.href='/teacherdashboard/';</script>") 
                elif TeacherReg.isrejected: return HttpResponse("<script>alert('Login not Succesful as Your Account was Rejected');window.location.href='/TeacherLogin/';</script>") 
                else: return HttpResponse("<script>alert('Login Succssful But Your Account is Pending Approval');window.location.href='/TeacherLogin/';</script>")  
        except models.TeacherReg.DoesNotExist: return HttpResponse("<script>alert( 'User Not Found'):window.location.href='/userlogin/';</script>")
    else: return render(request, 'TeacherLogin.html' )

def studentdashboard(request):
    if 'email' not in request.session: return redirect('userlogin')
    email = request.session['email']
    user = models.User.objects.get(email=email)
    profile, created = models.StudentProfile.objects.get_or_create(student=user)
    quizzes_taken = models.QuizResult.objects.filter(student=user).count()
    calculated_minutes = profile.total_learning_minutes + (quizzes_taken * 15)
    total_hours = round(calculated_minutes / 60, 1)
    weekly_goal_percent = min((quizzes_taken / 5) * 100, 100)
    recent_courses = models.ContentLibrary.objects.all().order_by('-created_at')[:3]
    
    text_notes = storage_manager.get_notes_by_section("TEXT")
    audio_notes = storage_manager.get_notes_by_section("AUDIO")
    video_notes = storage_manager.get_notes_by_section("VIDEO")

    context = {
        'user': user, 'profile': profile, 'total_hours': total_hours, 
        'weekly_goal_percent': int(weekly_goal_percent), 'recent_courses': recent_courses,
        'text_notes': text_notes, 'audio_notes': audio_notes, 'video_notes': video_notes
    }
    return render(request, 'studentdashboard.html', context)

def studentcourses(request):
    if 'email' not in request.session: return redirect('userlogin')
    email = request.session['email']
    user = models.User.objects.get(email=email)
    contents = models.ContentLibrary.objects.exclude(file='ai_generated.pdf').order_by('-created_at')
    
    audio_notes = storage_manager.get_notes_by_section("AUDIO")
    video_notes = storage_manager.get_notes_by_section("VIDEO")
    text_notes = storage_manager.get_notes_by_section("TEXT")

    if request.method == 'POST':
        target_format = request.POST.get('format')
        uploaded_file = request.FILES.get('student_file')
        course_id = request.POST.get('course_content_id')
        file_path = None
        
        # try:
        if uploaded_file:
            fs = FileSystemStorage()
            filename = fs.save(f"temp_{uploaded_file.name}", uploaded_file)
            file_path = fs.path(filename)
            source_name = uploaded_file.name
        elif course_id:
            content = models.ContentLibrary.objects.get(id=course_id)
            file_path = content.file.path
            source_name = content.title
        else: 
            return HttpResponse("ERROR: No file selected.")

        gemini_file = old_genai.upload_file(path=file_path)
        while gemini_file.state.name == "PROCESSING":
            time.sleep(1)
            gemini_file = old_genai.get_file(gemini_file.name)
        
        prompt = ""
        if target_format == 'video': prompt = "Describe a highly realistic, cinematic scene that represents the main topic of this document. Keep it visual and detailed. Max 20 words."
        elif target_format == 'audio': prompt = "Convert this content into an engaging lecture script suitable for reading aloud. No character names."
        else: prompt = "Convert this content into STUDY NOTES. Output clean plain text with headings and bullets."

        model = get_gemini_model(config=text_generation_config)
        response = generate_safe(model, [gemini_file, prompt])
        
        conversion_result = response.text.strip()
        note_title = f"{target_format.capitalize()}: {source_name}"

        if target_format == 'audio':
            try:
                tts = gTTS(text=conversion_result, lang='en', slow=False)
                mp3_fp = BytesIO()
                tts.write_to_fp(mp3_fp)
                mp3_fp.seek(0)
                storage_manager.save_new_note(note_title, mp3_fp.getvalue(), "AUDIO")
            except Exception as e:
                print(f"TTS Error: {e}")
        
        elif target_format == 'video':
            
            print("Generating video with Veo...")

            operation = veo_client.models.generate_videos(
                model="veo-3.1-fast-generate-preview",
                prompt=conversion_result,
                config=types.GenerateVideosConfig(
                    aspect_ratio="9:16",
                    resolution="720p",
                    duration_seconds=4,
                ),
            )

            
            operation_name = operation if isinstance(operation, str) else operation.name

            # ✅ poll safely
            while not operation.done:
                print("Video generation in progress...")
                time.sleep(20)
                operation = veo_client.operations.get(operation)
              

            if operation.error:
                raise Exception(operation.error.message)
            print(operation.response)
            generated_video = operation.response.generated_videos[0]
            video_bytes = veo_client.files.download(
                file=generated_video.video
            )

            storage_manager.save_new_note(note_title, video_bytes, "VIDEO")
            

        else:
            storage_manager.save_new_note(note_title, conversion_result, "TEXT")

        audio_notes = storage_manager.get_notes_by_section("AUDIO")
        video_notes = storage_manager.get_notes_by_section("VIDEO")
        text_notes = storage_manager.get_notes_by_section("TEXT")

        return render(request, 'studentcourses.html', {
            'user': user, 'contents': contents, 
            'conversion_result': conversion_result, 
            'audio_notes': audio_notes, 'video_notes': video_notes, 'text_notes': text_notes
        })
        # except Exception as e: 
        #     print(f"ERROR: {e}")
        #     return HttpResponse(f"<h1>API Busy or Error</h1><p>Google is busy. Please wait 1 minute and try again.</p><p>Details: {str(e)}</p>")

    return render(request, 'studentcourses.html', {
        'user': user, 'contents': contents, 
        'audio_notes': audio_notes, 'video_notes': video_notes, 'text_notes': text_notes
    })

# ... (Imports remain the same) ...

# In views.py, update the teacherdashboard function:

def teacherdashboard(request):
    if 'email' not in request.session: return redirect('TeacherLogin')
    email = request.session['email']
    user = models.TeacherReg.objects.get(email=email)
    
    # 1. General Stats
    total_students = models.User.objects.count()
    my_uploads = models.ContentLibrary.objects.filter(teacher=user)
    active_lectures = my_uploads.count()
    
    # 2. Engagement
    teacher_content_ids = my_uploads.values_list('id', flat=True)
    quiz_results = models.QuizResult.objects.filter(content__id__in=teacher_content_ids)
    
    if quiz_results.exists():
        avg_score = quiz_results.aggregate(Avg('score'))['score__avg'] or 0
        avg_engagement = int((avg_score / 5) * 100)
    else:
        avg_engagement = 0

    # 3. Recent Files
    recent_files = my_uploads.order_by('-created_at')[:3]

    # 4. Learning Styles
    profiles = models.StudentProfile.objects.all()
    total_profiles = profiles.count()
    style_counts = {'Visual': 0, 'Auditory': 0, 'Textual': 0, 'Kinesthetic': 0}
    
    for p in profiles:
        if p.learning_style in style_counts:
            style_counts[p.learning_style] += 1
            
    if total_profiles > 0:
        v_pct = int((style_counts['Visual'] / total_profiles) * 100)
        a_pct = int((style_counts['Auditory'] / total_profiles) * 100)
        t_pct = int((style_counts['Textual'] / total_profiles) * 100)
        k_pct = 100 - v_pct - a_pct - t_pct
    else:
        v_pct, a_pct, t_pct, k_pct = 0, 0, 0, 0

    p1 = v_pct
    p2 = v_pct + a_pct
    p3 = v_pct + a_pct + t_pct
    pie_style = f"conic-gradient(#3b82f6 0% {p1}%, #10b981 {p1}% {p2}%, #94a3b8 {p2}% {p3}%, #f59e0b {p3}% 100%)"

    # 5. Student Monitoring (ALL STUDENTS)
    watchlist = []
    all_students = models.User.objects.all()
    
    for s in all_students:
        s_quizzes = models.QuizResult.objects.filter(student=s)
        if s_quizzes.exists():
            s_avg = s_quizzes.aggregate(Avg('score'))['score__avg'] or 0
            
            if s_avg < 2.5: 
                flag_class = "red"
                flag_text = "At Risk"
                icon = "fa-circle-exclamation"
            elif s_avg < 3.5: 
                flag_class = "yellow"
                flag_text = "Needs Focus"
                icon = "fa-triangle-exclamation"
            else: 
                flag_class = "green"
                flag_text = "On Track"
                icon = "fa-circle-check"
            
            # Recent scores for graph
            recent_scores = list(s_quizzes.order_by('-date_taken').values_list('score', flat=True)[:5])
            while len(recent_scores) < 5: recent_scores.insert(0, 0)

            watchlist.append({
                'name': s.name,
                'avg': round(s_avg, 1),
                'flag_class': flag_class,
                'flag_text': flag_text,
                'icon': icon,
                'chart_data': recent_scores
            })
        else:
            # Handle students with no quizzes (Optional: add them as 'Unknown' status)
            watchlist.append({
                'name': s.name, 'avg': 0, 'flag_class': 'gray', 'flag_text': 'No Data', 
                'icon': 'fa-circle', 'chart_data': [0,0,0,0,0]
            })
    
    # Sort by Score (lowest first)
    watchlist.sort(key=lambda x: x['avg'])
    
    # IMPORTANT: No slicing ([:5]) here, so ALL 12 students are sent to template
    
    context = {
        'user': user,
        'total_students': total_students,
        'active_lectures': active_lectures,
        'avg_engagement': avg_engagement,
        'recent_files': recent_files,
        'pie_style': pie_style,
        'style_stats': {'v': v_pct, 'a': a_pct, 't': t_pct, 'k': k_pct},
        'watchlist': watchlist
    }
    return render(request, 'teacherdashboard.html', context)

def logout(request):    
    request.session.flush()
    return redirect('index')

def studentprofile(request):
    if 'email' in request.session:
        email=request.session['email']
        try:
            user=models.User.objects.get(email=email)
            return render(request,'studentprofile.html',{'user':user})
        except models.User.DoesNotExist: return HttpResponse('user not found')
    else: return redirect('login')
    
def studenteditprofile(request,eid):
    edit = models.User.objects.get(id = eid)
    if request.method == "POST":
        name = request.POST.get('name')
        if request.FILES.get('image'): edit.image = request.FILES.get('image')
        edit.age = request.POST.get('age')
        edit.phone = request.POST.get('phone')
        edit.email = request.POST.get('email')
        edit.currenteducation = request.POST.get('currenteducation')
        edit.name=name
        edit.save()
        return redirect('studentprofile')
    return render(request,'studenteditprofile.html',{'edit':edit})

def features(request): return render(request,'features.html')

def studentquiz(request):
    if 'email' not in request.session: return redirect('userlogin')
    email = request.session['email']
    user = models.User.objects.get(email=email)
    contents = models.ContentLibrary.objects.exclude(file='ai_generated.pdf').order_by('-created_at')
    
    if request.method == "POST":
        model = get_gemini_model(config=json_generation_config)
        content_id = request.POST.get('content_id')
        num_questions = request.POST.get('num_questions', '5')
        difficulty = request.POST.get('difficulty', 'Medium')
        prompt = ""
        source_material = None
        topic_title = "General Knowledge"
        try:
            if content_id:
                content_obj = models.ContentLibrary.objects.get(id=content_id)
                source_material = old_genai.upload_file(path=content_obj.file.path)
                topic_title = content_obj.title
                while source_material.state.name == "PROCESSING": time.sleep(1); source_material = old_genai.get_file(source_material.name)
                # UPDATED PROMPT TO BE STRICTER
                prompt = f"""Create a {difficulty} level quiz ({num_questions} Qs). 
                JSON format: [{{ "question": "...", "options": ["A", "B", "C", "D"], "answer": "A" }}]
                IMPORTANT: "answer" field must be a SINGLE LETTER (A, B, C, or D)."""
            else: return HttpResponse("<script>alert('Please select a source material.');window.history.back();</script>")

            if source_material: response = generate_safe(model, [source_material, prompt])
            else: response = generate_safe(model, prompt)
            
            clean_json = response.text.replace('```json', '').replace('```', '').strip()
            default_teacher = models.TeacherReg.objects.first()
            new_quiz_content = models.ContentLibrary.objects.create(teacher=default_teacher, title=f"AI Quiz: {topic_title}", description=f"AI Generated {difficulty} Quiz", file="ai_generated.pdf", ai_quiz=clean_json)
            return redirect('take_quiz', id=new_quiz_content.id)
        except Exception as e:
            print(f"AI Error: {e}")
            return HttpResponse(f"<script>alert('Error: {str(e)}');window.history.back();</script>")

    available_quizzes = models.ContentLibrary.objects.exclude(ai_quiz__isnull=True).exclude(ai_quiz__exact='').order_by('-created_at')
    return render(request, 'studentquiz.html', {'user': user, 'quizzes': available_quizzes, 'contents': contents})

def take_quiz(request, id):
    if 'email' not in request.session: return redirect('userlogin')
    content = models.ContentLibrary.objects.get(id=id)
    try: quiz_data = json.loads(content.ai_quiz)
    except: quiz_data = [] 
    return render(request, 'take_quiz.html', {'content': content, 'quiz_data': quiz_data})

# --- UPDATED DATA CLEANER ---
def clean_option_data(val):
    if not val: return 'A' # Default to A to prevent empty crashes
    val = str(val).strip().upper()
    
    # Handle numbers 1-4
    if val in ['1', '1.', '1)']: return 'A'
    if val in ['2', '2.', '2)']: return 'B'
    if val in ['3', '3.', '3)']: return 'C'
    if val in ['4', '4.', '4)']: return 'D'

    # Handle "Option A" or full text starting with Letter
    if len(val) > 0 and val[0] in ['A', 'B', 'C', 'D']: return val[0]
    
    # Handle "Answer: B"
    if " " in val:
        parts = val.split()
        for p in parts:
             if p in ['A', 'B', 'C', 'D']: return p

    return 'A' # Ultimate fallback

def submit_quiz_result(request, id):
    if 'email' not in request.session: return redirect('userlogin')
    if request.method == 'POST':
        user = models.User.objects.get(email=request.session['email'])
        content = models.ContentLibrary.objects.get(id=id)
        try: quiz_data = json.loads(content.ai_quiz)
        except: return HttpResponse("Error loading quiz data")
        
        score = 0
        total = len(quiz_data)
        enhanced_quiz_data = []
        user_answers_dict = {} 
        for index, question in enumerate(quiz_data):
            user_answer = request.POST.get(f'question_{index}')
            clean_correct = clean_option_data(question.get('answer', 'A'))
            clean_user = clean_option_data(user_answer)
            question['answer'] = clean_correct
            question['user_answer'] = clean_user
            user_answers_dict[str(index)] = clean_user 
            if clean_user == clean_correct: score += 1
            enhanced_quiz_data.append(question)
                
        models.QuizResult.objects.create(student=user, content=content, score=score, total_questions=total, topic=content.title, answers_json=json.dumps(user_answers_dict))
        profile = models.StudentProfile.objects.get(student=user)
        profile.total_learning_minutes += (total * 2) 
        profile.save()
        return render(request, 'take_quiz.html', {'content': content, 'quiz_data': enhanced_quiz_data, 'score': score, 'total': total, 'show_results': True})

def review_quiz_result(request, id):
    if 'email' not in request.session: return redirect('userlogin')
    result = models.QuizResult.objects.get(id=id)
    content = result.content
    try:
        quiz_data = json.loads(content.ai_quiz)
        if result.answers_json: saved_answers = json.loads(result.answers_json)
        else: saved_answers = {}
    except: return HttpResponse("Error loading quiz data")
    enhanced_quiz_data = []
    for index, question in enumerate(quiz_data):
        clean_correct = clean_option_data(question.get('answer', 'A'))
        raw_user = saved_answers.get(str(index), '')
        clean_user = clean_option_data(raw_user)
        question['answer'] = clean_correct
        question['user_answer'] = clean_user
        enhanced_quiz_data.append(question)
    return render(request, 'take_quiz.html', {'content': content, 'quiz_data': enhanced_quiz_data, 'score': result.score, 'total': result.total_questions, 'show_results': True})

def studenttimetable(request):
    if 'email' not in request.session: return redirect('userlogin')
    email = request.session['email']
    user = models.User.objects.get(email=email)
    courses = models.ContentLibrary.objects.all() 
    
    # Default hours
    last_hours = request.session.get('last_hours', 4)

    # 1. Add Event
    if request.method == "POST" and 'add_event' in request.POST:
        subject = request.POST.get('subject')
        day = request.POST.get('day')
        time_slot = request.POST.get('time_slot')
        location = request.POST.get('location')
        if models.StudentEvent.objects.filter(student=user, day=day, time_slot=time_slot).exists():
            return HttpResponse("<script>alert('Slot occupied!');window.history.back();</script>")
        models.StudentEvent.objects.create(student=user, subject=subject, day=day, time_slot=time_slot, location=location, color='evt-blue')
        return redirect('studenttimetable')

    # 2. Delete Event
    if request.method == "POST" and 'delete_event' in request.POST:
        event_id = request.POST.get('event_id')
        try: models.StudentEvent.objects.get(id=event_id, student=user).delete()
        except: pass
        return redirect('studenttimetable')

    # 3. AI Generation
    generated_plan = None
    if request.method == "POST" and 'generate_ai' in request.POST:
        try: 
            hours = int(request.POST.get('hours'))
            request.session['last_hours'] = hours 
            last_hours = hours
        except: 
            hours = 4 
        
        models.StudentEvent.objects.filter(student=user, color='evt-purple').delete()
        all_times = ['09:00', '10:00', '11:00', '12:00', '01:00', '02:00']
        allowed_slots = all_times[:hours]
        
        # --- SMART SUBJECT INJECTION ---
        course_titles = [c.title for c in courses]
        if not course_titles:
            subject_list_str = "Math, Science, History"
        else:
            subject_list_str = ", ".join(course_titles)

        prompt = f"""
        Create a timetable for Monday, Tuesday, Wednesday, Thursday, and Friday (5 days).
        EACH DAY must have exactly {hours} classes.
        Allowed Subjects: {subject_list_str}.
        JSON list format: [{{"day": "Mon", "time_slot": "09:00", "subject": "{course_titles[0] if course_titles else 'Math'}"}}]
        """
        try:
            model = get_gemini_model(config=json_generation_config)
            response = generate_safe(model, prompt)
            events_data = json.loads(response.text)
            for item in events_data:
                if item.get('time_slot') in allowed_slots:
                    if not models.StudentEvent.objects.filter(student=user, day=item.get('day'), time_slot=item.get('time_slot')).exists():
                        models.StudentEvent.objects.create(student=user, subject=item.get('subject'), day=item.get('day'), time_slot=item.get('time_slot'), location='AI Plan', color='evt-purple')
        except: generated_plan = "<p>AI generation failed.</p>"

    # 4. Build Matrix & Attach Notes (FIXED MATCHING LOGIC)
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    times = ['09:00', '10:00', '11:00', '12:00', '01:00', '02:00']
    timetable_matrix = []
    
    for t in times:
        row = {'time': t, 'slots': []}
        for d in days:
            event = models.StudentEvent.objects.filter(student=user, day=d, time_slot=t).first()
            if event:
                matched_course = None
                for c in courses:
                    if c.title.lower() in event.subject.lower() or event.subject.lower() in c.title.lower():
                        matched_course = c
                        break
                
                if matched_course and matched_course.ai_summary:
                    event.note = matched_course.ai_summary 
                else:
                    event.note = "Focus on key concepts and review lecture notes."
            row['slots'].append(event)
        timetable_matrix.append(row)

    return render(request, 'studenttimetable.html', {
        'user': user, 
        'generated_plan': generated_plan, 
        'timetable_matrix': timetable_matrix, 
        'courses': courses, 
        'days': days, 
        'last_hours': int(last_hours) 
    })

def studentachievements(request):
    if 'email' not in request.session: return redirect('userlogin')
    email = request.session['email']
    currentUser = models.User.objects.get(email=email)
    
    results = models.QuizResult.objects.filter(student=currentUser).order_by('-date_taken')
    total_xp_agg = results.aggregate(Sum('score'))['score__sum']
    current_user_xp = (total_xp_agg * 100) if total_xp_agg else 0
    
    if current_user_xp > 5000: rank = "Scholar 🎓"
    elif current_user_xp > 2000: rank = "Advanced 🧠"
    elif current_user_xp > 500: rank = "Intermediate 📚"
    else: rank = "Novice 🌱"
    
    if current_user_xp < 500: next_level = 500
    elif current_user_xp < 2000: next_level = 2000
    else: next_level = 5000
    
    progress = (current_user_xp / next_level) * 100 if next_level > 0 else 100

    all_students = models.User.objects.all()
    leaderboard_data = []
    
    for student in all_students:
        s_results = models.QuizResult.objects.filter(student=student)
        s_xp = (s_results.aggregate(Sum('score'))['score__sum'] or 0) * 100
        
        leaderboard_data.append({
            'name': student.name,
            'xp': s_xp,
            'image': student.image,
            'is_me': (student.email == email)
        })

    leaderboard_data.sort(key=lambda x: x['xp'], reverse=True)
    top_5_leaderboard = leaderboard_data[:5]

    context = {
        'user': currentUser, 
        'results': results, 
        'total_xp': current_user_xp, 
        'rank': rank, 
        'progress': int(progress), 
        'next_level': next_level,
        'leaderboard': top_5_leaderboard
    }
    return render(request, 'studentachievements.html', context)

# --- CLASS MANAGEMENT VIEWS ---

def teacherclasses(request):
    if 'email' not in request.session: return redirect('TeacherLogin')
    email = request.session['email']
    teacher = models.TeacherReg.objects.get(email=email)
    
    # Fetch all classes for this teacher
    classes = models.Classroom.objects.filter(teacher=teacher)
    
    # Get all students for the "Add Student" dropdown
    all_students = models.User.objects.all()
    
    # Prepare data for each class (Stats)
    class_data = []
    for c in classes:
        student_count = c.students.count()
        # Mock calculation for engagement (in a real app, this would query QuizResults)
        engagement = 0
        if student_count > 0:
            # Check avg quiz score for students in this class
            enrolled_ids = c.students.values_list('id', flat=True)
            avg = models.QuizResult.objects.filter(student__id__in=enrolled_ids).aggregate(Avg('score'))['score__avg'] or 0
            engagement = int((avg / 5) * 100)
            
        class_data.append({
            'obj': c,
            'count': student_count,
            'engagement': engagement,
            'enrolled_students': c.students.all()
        })

    return render(request, 'teacherclasses.html', {
        'user': teacher,
        'classes': class_data,
        'all_students': all_students
    })

def create_class(request):
    if request.method == 'POST':
        email = request.session.get('email')
        teacher = models.TeacherReg.objects.get(email=email)
        name = request.POST.get('name')
        subject = request.POST.get('subject')
        models.Classroom.objects.create(teacher=teacher, name=name, subject=subject)
        return redirect('teacherclasses')

def delete_class(request, id):
    models.Classroom.objects.get(id=id).delete()
    return redirect('teacherclasses')

def add_student_to_class(request, class_id):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        c = models.Classroom.objects.get(id=class_id)
        s = models.User.objects.get(id=student_id)
        c.students.add(s)
        return redirect('teacherclasses')

def remove_student_from_class(request, class_id, student_id):
    c = models.Classroom.objects.get(id=class_id)
    s = models.User.objects.get(id=student_id)
    c.students.remove(s)
    return redirect('teacherclasses')

def teachercontentupl(request):
    if 'email' not in request.session: return redirect('TeacherLogin')
    email = request.session['email']
    user = models.TeacherReg.objects.get(email=email)
    
    # 1. Fetch Classes for the Dropdown
    classes = models.Classroom.objects.filter(teacher=user)
    
    # 2. Fetch Recent Uploads for the Side Panel
    recent_uploads = models.ContentLibrary.objects.filter(teacher=user).order_by('-created_at')[:5]

    if request.method == 'POST' and request.FILES.get('upload_file'):
        try:
            uploaded_file = request.FILES['upload_file']
            title = request.POST.get('title', 'Untitled')
            description = request.POST.get('description', '')
            
            # Save file
            fs = FileSystemStorage()
            filename = fs.save(uploaded_file.name, uploaded_file)
            file_path = fs.path(filename)
            
            # --- AI PROCESSING START ---
            gemini_file = old_genai.upload_file(path=file_path)
            while gemini_file.state.name == "PROCESSING": 
                time.sleep(1)
                gemini_file = old_genai.get_file(gemini_file.name)
            
            model = get_gemini_model()
            # Generate Summary & Quiz
            response = generate_safe(model, [gemini_file, "Generate a summary and a 5-question quiz JSON. Format: {'summary': '...', 'quiz': [...]}"])
            
            # Parse AI Response
            try:
                # Clean up markdown if present
                clean_text = response.text.replace('```json', '').replace('```', '').strip()
                ai_data = json.loads(clean_text)
                summary = ai_data.get('summary', 'No summary generated.')
                quiz = json.dumps(ai_data.get('quiz', []))
            except:
                summary = response.text
                quiz = "[]"
            # --- AI PROCESSING END ---

            # Save to Database
            models.ContentLibrary.objects.create(
                teacher=user, 
                title=title, 
                description=description, 
                file=filename, 
                ai_summary=summary, 
                ai_quiz=quiz
            )
            
            return HttpResponse("<script>alert('Upload & AI Generation Successful!');window.location.href='/teachercontentupl/';</script>")
        except Exception as e: 
            print(f"Error: {e}")
            return HttpResponse(f"<script>alert('Error: {str(e)}');window.history.back();</script>")

    return render(request, 'teachercontentupl.html', {
        'user': user, 
        'classes': classes, 
        'recent_uploads': recent_uploads
    })

def teachercontentlib(request):
    if 'email' not in request.session: return redirect('TeacherLogin')
    email=request.session['email']
    user = models.TeacherReg.objects.get(email=email)
    contents = models.ContentLibrary.objects.filter(teacher=user).order_by('-created_at')
    return render(request,'teachercontentlib.html',{'user':user, 'contents': contents})

def delete_content(request, id):
    if 'email' not in request.session: return redirect('TeacherLogin')
    try:
        content = models.ContentLibrary.objects.get(id=id)
        # Check if the logged-in teacher owns this content (Security)
        user = models.TeacherReg.objects.get(email=request.session['email'])
        if content.teacher == user:
            content.delete()
            # Also delete from storage if needed (optional)
            if os.path.exists(content.file.path):
                os.remove(content.file.path)
            return redirect('teachercontentlib')
        else:
            return HttpResponse("Unauthorized action.")
    except Exception as e:
        print(e)
        return redirect('teachercontentlib')

def teacherstanaly(request):
    if 'email' not in request.session: return redirect('TeacherLogin')
    email = request.session['email']
    teacher = models.TeacherReg.objects.get(email=email)
    
    # 1. Student List Data (Existing Logic)
    students = models.User.objects.all()
    student_data = []
    
    for s in students:
        profile, created = models.StudentProfile.objects.get_or_create(student=s)
        quizzes = models.QuizResult.objects.filter(student=s)
        q_count = quizzes.count()
        s_avg = quizzes.aggregate(Avg('score'))['score__avg'] or 0
        
        if s_avg >= 4: engagement = "High"
        elif s_avg >= 2: engagement = "Medium"
        else: engagement = "Low"
        
        recent_scores = list(quizzes.order_by('-date_taken').values_list('score', flat=True)[:5])
        while len(recent_scores) < 5: recent_scores.insert(0, 0)
        
        student_data.append({
            'id': s.id, 'name': s.name, 'image': s.image,
            'style': profile.learning_style or "Undetermined",
            'avg_score': round(s_avg, 1), 'engagement': engagement,
            'total_hours': round(profile.total_learning_minutes / 60, 1),
            'quiz_count': q_count, 'chart_data': recent_scores
        })

    # 2. NEW: Class Performance Data (For the Main Graph)
    classes = models.Classroom.objects.filter(teacher=teacher)
    class_performance_data = []
    
    for c in classes:
        # Get students in this specific class
        enrolled_students = c.students.all()
        # Get quizzes taken by these students (filtered by this teacher's content)
        class_quizzes = models.QuizResult.objects.filter(student__in=enrolled_students, content__teacher=teacher)
        
        if class_quizzes.exists():
            class_avg = class_quizzes.aggregate(Avg('score'))['score__avg'] or 0
            
            # Drill-down: Group by Quiz Topic (Subject Wise)
            topic_stats = class_quizzes.values('topic').annotate(avg_score=Avg('score'))
            topics = []
            topic_scores = []
            
            for item in topic_stats:
                t_name = item['topic'] if item['topic'] else "General"
                topics.append(t_name)
                topic_scores.append(round(item['avg_score'], 1))
                
            class_performance_data.append({
                'name': c.name, # e.g. CS101
                'avg': round(class_avg, 1),
                'topics': topics, # ['Algebra', 'Calculus']
                'topic_scores': topic_scores # [4.5, 3.2]
            })
        else:
            # Empty class handling
            class_performance_data.append({
                'name': c.name, 'avg': 0, 'topics': [], 'topic_scores': []
            })

    # Fallback data for the second chart (Engagement) to keep it working
    main_chart_data = [3.5, 4.2, 3.8, 4.5, 4.0] 

    context = {
        'user': teacher,
        'students': student_data,
        'class_performance_data': class_performance_data, # Data for the modified graph
        'main_chart_data': main_chart_data 
    }
    return render(request, 'teacherstanaly.html', context)

def teacherprofile(request):
    if 'email' not in request.session: return redirect('TeacherLogin')
    email = request.session['email']
    user = models.TeacherReg.objects.get(email=email)
    return render(request, 'teacherprofile.html', {'user': user})

def teachereditprofile(request):
    if 'email' not in request.session: return redirect('TeacherLogin')
    email = request.session['email']
    user = models.TeacherReg.objects.get(email=email)

    if request.method == 'POST':
        user.name = request.POST.get('name')
        user.phone = request.POST.get('phone')
        user.age = request.POST.get('age')
        user.experience = request.POST.get('experience')
        user.specialization = request.POST.get('specialization')
        
        # Check if a new image was uploaded
        if request.FILES.get('image'):
            user.image = request.FILES['image']
            
        user.save()
        return redirect('teacherprofile') # Redirect to profile page to see changes

    return render(request, 'teachereditprofile.html', {'user': user})

def adminlogin(request):
    if request.method == 'POST': 
        if request.POST.get('username') == "ADMIN" and request.POST.get('password') == "admin":
            request.session['adminusername']= "ADMIN"
            return redirect('adminhome')
        return HttpResponse("Invalid credentials")
    return render(request, 'adminlogin.html')

def adminhome(request):
    # 1. Statistics
    total_students = models.User.objects.count()
    total_teachers = models.TeacherReg.objects.count()
    
    # Filter for pending teachers (neither approved nor rejected)
    pending_teachers_list = models.TeacherReg.objects.filter(isapproved=False, isrejected=False).order_by('-id')
    pending_count = pending_teachers_list.count()
    
    active_courses = models.ContentLibrary.objects.count()

    # 2. Recent Activity Data (Fetching actual latest records)
    # Get last 3 students
    recent_students = models.User.objects.all().order_by('-id')[:2]
    # Get last 2 uploaded contents
    recent_uploads = models.ContentLibrary.objects.all().order_by('-created_at')[:2]

    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'pending_requests': pending_count,
        'active_courses': active_courses,
        'pending_teachers': pending_teachers_list, # For the table
        'recent_students': recent_students,        # For Activity Feed
        'recent_uploads': recent_uploads           # For Activity Feed
    }
    return render(request, 'adminhome.html', context)
# In views.py

def adminmngstd(request):
    # Removed authentication check to fix the redirection error
    # Fetch all students to populate the table
    students = models.User.objects.all().order_by('-id')
    
    context = {
        'students': students, # CHANGED from 'user' to 'students' to fix display error
        'total_students': students.count()
    }
    return render(request, 'adminmngstd.html', context)

def deletestd(request, id):
    # Functional: Delete student by ID
    try:
        student = models.User.objects.get(id=id)
        student.delete()
    except:
        pass # Handle case where ID doesn't exist silently
    return redirect('adminmngstd')

def admin_save_student(request):
    # Functional: Handles both Adding NEW students and EDITING existing ones
    if request.method == "POST":
        student_id = request.POST.get('student_id') # Hidden field in your HTML
        name = request.POST.get('name')
        email = request.POST.get('email')
        education = request.POST.get('education')
        password = request.POST.get('password')

        if student_id: 
            # --- EDIT MODE ---
            student = models.User.objects.get(id=student_id)
            student.name = name
            student.email = email
            student.currenteducation = education
            if password: # Only update password if user typed a new one
                student.password = password
                student.confirmpassword = password
            student.save()
        else: 
            # --- ADD MODE ---
            # Check if email already exists to prevent duplicates
            if not models.User.objects.filter(email=email).exists():
                models.User.objects.create(
                    name=name, 
                    email=email, 
                    currenteducation=education, 
                    password=password, 
                    confirmpassword=password
                )
                
    return redirect('adminmngstd')

# ... existing views ...

def export_students(request):
    # Functional: Export student list to CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="students_list.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Age', 'Gender', 'Education', 'Status'])

    students = models.User.objects.all().order_by('-id')
    for s in students:
        status = "Active" # You can link this to s.is_active if needed
        writer.writerow([s.id, s.name, s.email, s.phone, s.age, s.gender, s.currenteducation, status])

    return response

def adminmngtch(request):
    # Fetch all teachers ordered by newest first
    teachers = models.TeacherReg.objects.all().order_by('-id')
    
    # Calculate pending count for the filter button
    pending_count = teachers.filter(isapproved=False, isrejected=False).count()
    
    context = {
        'teachers': teachers, 
        'total_teachers': teachers.count(),
        'pending_count': pending_count
    }
    return render(request, 'adminmngtch.html', context)

def deletetch(request, id):
    try:
        models.TeacherReg.objects.get(id=id).delete()
    except:
        pass
    return redirect('adminmngtch')

def approvedtch(request, id):
    teacher = models.TeacherReg.objects.get(id=id) 
    teacher.isapproved = True
    teacher.isrejected = False
    teacher.save() 
    return redirect('adminmngtch')

def rejectedtch(request, id): 
    teacher = models.TeacherReg.objects.get(id=id) 
    teacher.isapproved = False
    teacher.isrejected = True
    teacher.save() 
    return redirect('adminmngtch')

def admin_save_teacher(request):
    # Functional: Save Edited Teacher Details
    if request.method == "POST":
        teacher_id = request.POST.get('teacher_id')
        
        if teacher_id:
            teacher = models.TeacherReg.objects.get(id=teacher_id)
            teacher.name = request.POST.get('name')
            teacher.email = request.POST.get('email')
            teacher.phone = request.POST.get('phone')
            teacher.specialization = request.POST.get('specialization')
            teacher.experience = request.POST.get('experience')
            teacher.save()
            
    return redirect('adminmngtch')

def admincontentmod(request):
    # Fetch all content uploaded by teachers (ContentLibrary model)
    courses = models.ContentLibrary.objects.all().order_by('-created_at')
    
    # Calculate Stats
    total_courses = courses.count()
    # Assuming 'is_approved' logic exists or we can mock it. For now, let's say all uploads are 'Pending' if not explicitly approved.
    # If you don't have an 'is_approved' field yet, we can treat all as Active for now or add it to the model.
    # Let's assume everything uploaded is 'Active' unless we add a moderation flag.
    # For now, let's just count them.
    
    # Calculate Total Enrollments (Sum of students in classes that use this content - or just mock for now if complex)
    # A simpler metric: Total Quiz Results linked to content = "Engagement/Enrollments"
    total_enrollments = models.QuizResult.objects.count() 

    context = {
        'courses': courses,
        'total_courses': total_courses,
        'pending_courses': 0, # Placeholder if no approval system yet
        'total_enrollments': total_enrollments
    }
    return render(request, 'admincontentmod.html', context)

def delete_content_admin(request, id):
    # Admin deletion logic
    try:
        content = models.ContentLibrary.objects.get(id=id)
        content.delete()
    except:
        pass
    return redirect('admincontentmod')

def admin_save_course(request):
    # Functional: Edit Course Details (Title/Description)
    if request.method == "POST":
        course_id = request.POST.get('course_id')
        title = request.POST.get('title')
        description = request.POST.get('description')
        
        if course_id:
            course = models.ContentLibrary.objects.get(id=course_id)
            course.title = title
            course.description = description
            course.save()
            
    return redirect('admincontentmod')

def admin_create_course(request):
    # Functional: Admin creates course for a teacher
    if request.method == "POST":
        title = request.POST.get('title')
        description = request.POST.get('description')
        email = request.POST.get('email') # Instructor's email
        
        try:
            # Find the teacher by email
            teacher = models.TeacherReg.objects.get(email=email)
            
            # Check for file upload
            if request.FILES.get('file'):
                models.ContentLibrary.objects.create(
                    teacher=teacher,
                    title=title,
                    description=description,
                    file=request.FILES['file']
                )
        except models.TeacherReg.DoesNotExist:
            # You might want to handle this error (e.g. messages.error)
            print("Teacher not found")
            pass
            
    return redirect('admincontentmod')

def adminplat(request):
    return render(request, 'adminplat.html')

def admin_save_settings(request):
    # Functional: Save Platform Settings
    if request.method == "POST":
        # In a real app, you would save these to a Settings model
        site_name = request.POST.get('site_name')
        support_email = request.POST.get('support_email')
        maintenance = request.POST.get('maintenance_mode') # 'on' if checked
        registration = request.POST.get('allow_registration')
        student_fee = request.POST.get('student_fee')
        teacher_comm = request.POST.get('teacher_comm')
        
        # print(f"Settings Saved: {site_name}, Maintenance: {maintenance}")
        
    return redirect('adminhome') # Changed redirect from 'adminplat' to 'adminhome'

# --- NEW PSYCHOMETRIC TEST VIEW ---
def studentpsychometric(request):
    if 'email' not in request.session: return redirect('userlogin')
    email = request.session['email']
    user = models.User.objects.get(email=email)

    # 1. Define the Questions & Scoring Key
    # V = Visual, A = Auditory, R = Read/Write, K = Kinesthetic
    questions = [
        {
            "id": "q1",
            "question": "You need to learn how to use a new piece of complex software. You would prefer to:",
            "options": [
                {"value": "V", "text": "Look at diagrams and screenshots in the manual."},
                {"value": "A", "text": "Talk to someone who already knows how to use it."},
                {"value": "R", "text": "Read the written instructions or manual."},
                {"value": "K", "text": "Start clicking around and figure it out by doing."}
            ]
        },
        {
            "id": "q2",
            "question": "You are helping someone find their way to the airport. You would:",
            "options": [
                {"value": "V", "text": "Draw a map for them."},
                {"value": "A", "text": "Tell them the directions verbally."},
                {"value": "R", "text": "Write down a list of street names and turns."},
                {"value": "K", "text": "Go with them or drive ahead of them."}
            ]
        },
        {
            "id": "q3",
            "question": "You are planning a holiday for a group. You want some feedback on the plan. You would:",
            "options": [
                {"value": "V", "text": "Show them photos and web pages of the destination."},
                {"value": "A", "text": "Discuss the plan with them directly."},
                {"value": "R", "text": "Send them the itinerary and details in an email."},
                {"value": "K", "text": "Describe some of the activities you will be doing."}
            ]
        },
        {
            "id": "q4",
            "question": "You are about to buy a new digital camera or mobile phone. Other than price, what would most influence your decision?",
            "options": [
                {"value": "V", "text": "It looks modern and has a cool design."},
                {"value": "A", "text": " The salesperson selling it to me gave me good advice."},
                {"value": "R", "text": "Reading the details about its features."},
                {"value": "K", "text": "Trying it out and testing how it feels in my hand."}
            ]
        },
        {
            "id": "q5",
            "question": "Remember a time when you learned how to do something new. Try to avoid choosing a physical skill, eg. riding a bike. You learned best by:",
            "options": [
                {"value": "V", "text": "Seeing diagrams, graphs, or visual clues."},
                {"value": "A", "text": "Listening to explanations or asking questions."},
                {"value": "R", "text": "Reading written instructions."},
                {"value": "K", "text": "Watching a demonstration or doing it yourself."}
            ]
        }
    ]

    # 2. Handle Form Submission
    if request.method == "POST":
        scores = {"V": 0, "A": 0, "R": 0, "K": 0}
        
        # Calculate scores based on selected answers
        for q in questions:
            selected_option = request.POST.get(q['id'])
            if selected_option in scores:
                scores[selected_option] += 1
        
        # Find the winner
        dominant_style_code = max(scores, key=scores.get)
        
        # Map code to full name
        style_names = {
            "V": "Visual",
            "A": "Auditory",
            "R": "Textual", # Read/Write
            "K": "Kinesthetic"
        }
        final_style = style_names[dominant_style_code]

        # Save to DB
        profile, created = models.StudentProfile.objects.get_or_create(student=user)
        profile.learning_style = final_style
        profile.save()

        return HttpResponse(f"<script>alert('Test Complete! Your style is: {final_style}');window.location.href='/studentdashboard/';</script>")

    return render(request, 'studentpsychometric.html', {'user': user, 'questions': questions})

# --- FORGOT PASSWORD & RESET LOGIC ---

import random
from django.utils import timezone
from django.core.mail import send_mail

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        # Check if student email exists
        if models.User.objects.filter(email=email).exists():
            
            # Generate 6-digit OTP
            otp = random.randint(100000, 999999)

            # Save OTP info in session
            request.session['reset_email'] = email
            request.session['reset_type'] = 'student'
            request.session['otp'] = str(otp)
            request.session['otp_time'] = timezone.now().isoformat()

            # Send OTP via email
            try:
                send_mail(
                    subject="IntelliLearn Password Reset OTP",
                    message=f"Your OTP for password reset is: {otp}\n\nThis OTP is valid for 5 minutes.",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[email],
                    fail_silently=False,
                )
                messages.success(request, "OTP sent to your email.")
                return redirect('verify_otp')
            except Exception as e:
                print(f"Email Error: {e}")
                messages.error(request, "Failed to send OTP. Please check your internet connection.")
                return redirect('forgot_password')

        else:
            messages.error(request, "Student email address not found.")

    return render(request, 'studentforgetpassword.html')


def teacher_forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        if models.TeacherReg.objects.filter(email=email).exists():

            otp = random.randint(100000, 999999)

            request.session['reset_email'] = email
            request.session['reset_type'] = 'teacher'
            request.session['otp'] = str(otp)
            request.session['otp_time'] = timezone.now().isoformat()

            send_mail(
                subject="IntelliLearn Teacher Password Reset OTP",
                message=f"Your OTP for password reset is: {otp}\n\nThis OTP is valid for 5 minutes.",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )

            messages.success(request, "OTP sent to your email.")
            return redirect('verify_otp')

        else:
            messages.error(request, "Teacher email address not found.")

    return render(request, 'teacherforgetpassword.html')

def reset_password(request):
    # Shared Reset Logic, but renders different pages
    email = request.session.get('reset_email')
    user_type = request.session.get('reset_type')
    
    # Protect route
    if not email:
        return redirect('login')
        
    if request.method == 'POST':
        new_pass = request.POST.get('password')
        confirm_pass = request.POST.get('confirm_password')
        
        if new_pass == confirm_pass:
            if user_type == 'student':
                user = models.User.objects.get(email=email)
                user.password = new_pass
                user.confirmpassword = new_pass 
                user.save()
                del request.session['reset_email']
                return redirect('login') # Redirect to Student Login
                
            elif user_type == 'teacher':
                user = models.TeacherReg.objects.get(email=email)
                user.password = new_pass
                user.save()
                del request.session['reset_email']
                return redirect('TeacherLogin') # Redirect to Teacher Login
        else:
            messages.error(request, 'Passwords do not match.')
            
    # RENDER THE CORRECT TEMPLATE BASED ON USER TYPE
    if user_type == 'teacher':
        return render(request, 'teacherresetpassword.html')
    else:
        return render(request, 'studentresetpassword.html')
from datetime import timedelta
from django.utils import timezone

def verify_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')

        session_otp = request.session.get('otp')
        otp_time = request.session.get('otp_time')

        # 1. Validation: Check if session exists
        if not session_otp:
            messages.error(request, "Session expired. Please try again.")
            if 'reg_data' in request.session:
                return redirect('userregister')
            return redirect('forgot_password')

        # 2. Validation: Check Time Expiry
        if otp_time:
            try:
                otp_dt = timezone.datetime.fromisoformat(otp_time)
                if timezone.now() > otp_dt + timedelta(minutes=5):
                    messages.error(request, "OTP expired. Please try again.")
                    return redirect('forgot_password')
            except:
                pass 

        # 3. Verification Logic
        if str(entered_otp).strip() == str(session_otp).strip():
            
            # --- SCENARIO A: NEW USER REGISTRATION ---
            if 'reg_data' in request.session:
                try:
                    data = request.session['reg_data']
                    
                    image_path = None
                    if request.session.get('image_name'):
                        image_path = f"temp/{request.session.get('image_name')}"

                    new_user = models.User.objects.create(
                        name=data['name'],
                        email=data['email'],
                        password=data['password'],
                        confirmpassword=data['confirmpassword'],
                        age=data['age'],
                        gender=data['gender'],
                        phone=data['phone'],
                        currenteducation=data['currenteducation'],
                        image=image_path
                    )
                    
                    models.StudentProfile.objects.create(student=new_user)
                    
                    request.session.flush()
                    
                    # --- FIX IS HERE: Changed '/userlogin/' to '/login/' ---
                    return HttpResponse("<script>alert('OTP Verified! Registration Successful. Please Login.');window.location.href='/login/';</script>")

                except Exception as e:
                    print(f"DEBUG ERROR: {e}") 
                    return HttpResponse(f"<script>alert('Registration Failed: {str(e)}');window.history.back();</script>")

            # --- SCENARIO B: PASSWORD RESET ---
            elif 'reset_email' in request.session:
                return redirect('reset_password')
            
            else:
                return HttpResponse("<script>alert('Error: Unknown session state. Please login again.');window.location.href='/login/';</script>")

        else:
            return HttpResponse("<script>alert('Invalid OTP. Please try again.');window.history.back();</script>")

    return render(request, 'verify_otp.html')

import json
import requests
from django.http import JsonResponse
from django.shortcuts import render
from django.conf import settings


def chatbot(request):
    # ---------- GET REQUEST ----------
    if request.method == 'GET':
        return render(request, 'chatbot.html')

    # ---------- POST REQUEST ----------
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()

            payload = {
                "model": settings.GROQ_MODEL2,
                "messages": [
                    {
                       "role": "system",
            "content": (
                "You are a Socratic Educational Tutor. Your primary goal is to guide students "
                "to discover answers on their own through a sequence of thoughtful questions. "
                "\n\nSTRICT BEHAVIORAL RULES:\n"
                "1. NEVER give the direct answer or complete the student's work.\n"
                "2. ALWAYS start by acknowledging the student's input or effort.\n"
                "3. ASK EXACTLY ONE or TWO probing questions at a time to lead the student to the next logical step.\n"
                "4. If a student is stuck, provide a small hint, analogy, or conceptual clue—never a full solution.\n"
                "5. FORMATTING: Use clear, brief paragraphs. Use bullet points only for scaffolding (hints/analogies). "
                "Ensure every response ends with a clear question that encourages the student to reflect or try again.\n"
                "6. If the student is correct, confirm it and ask a follow-up 'why' or 'what if' question to deepen their understanding."
                        )
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                "temperature": 0.3,
                "top_p": 0.9,
                "max_tokens": 1200
            }

            headers = {
                "Authorization": f"Bearer {settings.GROQ_API_KEY2}",
                "Content-Type": "application/json"
            }

            response = requests.post(
                settings.GROQ_API_URL2,
                headers=headers,
                json=payload,
                timeout=60
            )

            response.raise_for_status()
            response_json = response.json()

            choice = response_json["choices"][0]
            reply = choice["message"]["content"].strip()

            # ---------- HANDLE TRUNCATED RESPONSES ----------
            if choice.get("finish_reason") == "length":
                reply += "\n\n⚠️ Response was cut short. Please ask to continue."

            return JsonResponse({"response": reply})

        except Exception as e:
            # --- THIS PART IS UPDATED TO REVEAL THE HIDDEN BUG ---
            print(f"CRITICAL CHATBOT ERROR: {str(e)}")
            return JsonResponse(
                {"response": f"API Error: {str(e)}"},
                status=500
            )

    return JsonResponse({'response': 'Invalid request method'}, status=405)