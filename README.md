# IntelliLearn – AI-Powered Adaptive Learning Platform

IntelliLearn is a full-stack educational web application designed to deliver personalized learning paths and automated evaluations based on dynamic student performance metrics.

---

## Key Highlights & Features
- **Adaptive Evaluation Engine:** Analyzes student interaction data to dynamically calibrate quiz difficulty and recommend tailored review materials.
- **Role-Based Authentication:** Dedicated dashboards with secure session handling for students, instructors, and system administrators.
- **Relational Data Architecture:** Normalized schema to track student progress logs, assessment scores, and engagement metrics.
- **RESTful Endpoints:** Structured APIs for asynchronous submission of evaluation tests and dynamic metric calculation.
- **Performance Optimized:** Clean query design using Django ORM to maintain fast response times.

---

## Tech Stack
- **Backend:** Python, Django
- **Database:** PostgreSQL / SQLite
- **Frontend:** HTML5, CSS3, JavaScript
- **API Architecture:** Django REST Framework / JSON API views
- **Version Control & Tools:** Git, Visual Studio Code, Postman

---

## Project Structure
```text
intellilearn-platform/
│
├── accounts/         # Authentication, user models, role management
├── assessments/      # Core logic for adaptive testing and scoring
├── dashboard/        # Student progress reporting and visualization views
├── templates/        # HTML templates and UI components
├── static/           # CSS stylesheets, JavaScript scripts, and assets
├── manage.py
└── requirements.txt
