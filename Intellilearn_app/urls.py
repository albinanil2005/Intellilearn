from django.urls import path
from . import views

urlpatterns=[
    path('',views.index,name='index'),
    path('index/',views.index,name='index'),
    path('register/',views.userregister,name='register'),
    path('login/',views.userlogin,name='login'),
    
    # --- PASSWORD RESET FLOWS ---
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('forgot-password/', views.forgot_password, name='forgot_password'), # Student verify
    path('teacher-forgot-password/', views.teacher_forgot_password, name='teacher_forgot_password'), # Teacher verify
    path('reset-password/', views.reset_password, name='reset_password'), # Shared reset page
    
    # Student Dashboard & Features
    path('studentdashboard/',views.studentdashboard,name='studentdashboard'),
    path('studentcourses/',views.studentcourses,name='studentcourses'),
    path('studentquiz/',views.studentquiz,name='studentquiz'),
    path('studenttimetable/',views.studenttimetable,name='studenttimetable'),
    path('studentachievements/',views.studentachievements,name='studentachievements'),
    path('studentprofile/',views.studentprofile,name='studentprofile'),
    path('studenteditprofile/<int:eid>/',views.studenteditprofile,name='studenteditprofile'),
    # --- ADDED PSYCHOMETRIC TEST URL ---
    path('studentpsychometric/', views.studentpsychometric, name='studentpsychometric'),

    # Teacher Dashboard & Features
    path('teacherdashboard/',views.teacherdashboard,name='teacherdashboard'),
    path('teacherclasses/',views.teacherclasses,name='teacherclasses'),
    
    # --- ADDED CLASS MANAGEMENT URLS ---
    path('create_class/', views.create_class, name='create_class'),
    path('delete_class/<int:id>/', views.delete_class, name='delete_class'),
    path('add_student_to_class/<int:class_id>/', views.add_student_to_class, name='add_student_to_class'),
    path('remove_student_from_class/<int:class_id>/<int:student_id>/', views.remove_student_from_class, name='remove_student_from_class'),

    path('teachercontentupl/',views.teachercontentupl,name='teachercontentupl'),
    path('teachercontentlib/',views.teachercontentlib,name='teachercontentlib'),
    # --- ADDED CONTENT DELETION URL ---
    path('delete_content/<int:id>/', views.delete_content, name='delete_content'),
    
    path('teacherprofile/',views.teacherprofile,name='teacherprofile'),
    path('teachereditprofile/',views.teachereditprofile,name='teachereditprofile'),
    path('teacherstanaly/',views.teacherstanaly,name='teacherstanaly'),
    path('TeacherReg/',views.TeacherReg,name='TeacherReg'),
    path('TeacherLogin/',views.TeacherLogin,name='TeacherLogin'),

    # Admin & Common
    path('logout/',views.logout,name='logout'),
    path('features/',views.features,name='features'),
    path('adminlogin/',views.adminlogin,name='adminlogin'),
    path('adminhome/',views.adminhome,name='adminhome'),
    
    path('adminmngstd/',views.adminmngstd,name='adminmngstd'),
    path('deletestd/<int:id>/',views.deletestd,name='deletestd'),
    # --- ADDED ADMIN SAVE STUDENT URL ---
    path('admin_save_student/', views.admin_save_student, name='admin_save_student'),
    path('export_students/', views.export_students, name='export_students'),

    path('adminmngtch/',views.adminmngtch,name='adminmngtch'),
    path('deletetch/<int:id>/',views.deletetch,name='deletetch'),
    path('admin_save_teacher/', views.admin_save_teacher, name='admin_save_teacher'),
    path('admincontentmod/',views.admincontentmod,name='admincontentmod'),
    path('delete_content_admin/<int:id>/', views.delete_content_admin, name='delete_content_admin'),
    path('admin_save_course/', views.admin_save_course, name='admin_save_course'),
    path('admin_create_course/', views.admin_create_course, name='admin_create_course'),
    path('adminplat/',views.adminplat,name='adminplat'),
    path('admin_save_settings/', views.admin_save_settings, name='admin_save_settings'),
    path('approvedtch/<int:id>/', views.approvedtch, name='approvedtch'),
    path('rejectedtch/<int:id>/', views.rejectedtch, name='rejectedtch'),

    # Quiz Functionality
    path('take_quiz/<int:id>/', views.take_quiz, name='take_quiz'),
    path('submit_quiz_result/<int:id>/', views.submit_quiz_result, name='submit_quiz_result'),
    path('review_quiz_result/<int:id>/', views.review_quiz_result, name='review_quiz_result'),
    
    path('chatbot/', views.chatbot, name='chatbot'),

]