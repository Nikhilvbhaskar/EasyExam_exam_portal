from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '7633',
    'database': 'exam_portal'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# Routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/exam_list')
def exam_list():
    # Query all exams from the database
    exams = Exam.query.all()  # Assuming you are using SQLAlchemy and have defined the Exam model

    # Render the exam list template and pass the exams to it
    return render_template('exam_list.html', exams=exams)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user and user['password'] == password:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')


@app.route('/take_exam/<int:exam_id>', methods=['GET', 'POST'])
def take_exam(exam_id):
    # Fetch the exam and questions by exam_id
    exam = Exam.query.get(exam_id)
    questions = Question.query.filter_by(exam_id=exam_id).all()

    if request.method == 'POST':
        # Handle form submission (process answers)
        # Redirect or provide feedback after submission
        pass

    # Render the take exam template
    return render_template('take_exam.html', exam=exam, questions=questions)


@app.route('/view_results')
def view_results():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if 'role' in session:
        if session['role'] == 'student':
            # Fetch results for the logged-in student
            cursor.execute("SELECT exams.exam_name, results.score, results.total_questions, results.submission_time "
                           "FROM results JOIN exams ON results.exam_id = exams.id WHERE results.student_id=%s",
                           (session['user_id'],))
        elif session['role'] == 'admin':
            # Fetch all results for admins
            cursor.execute("SELECT users.username, exams.exam_name, results.score, results.total_questions, results.submission_time "
                           "FROM results JOIN exams ON results.exam_id = exams.id "
                           "JOIN users ON results.student_id = users.id")
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('view_results.html', results=results)

    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']  # Choose 'student' or 'admin'

        # Insert new user directly (without hashing)
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", 
                           (username, password, role))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash('Error: Username already exists or invalid input.', 'danger')
        finally:
            cursor.close()
            conn.close()
    return render_template('register.html')


@app.route('/dashboard')
def dashboard():
    if 'role' in session:
        if session['role'] == 'admin':
            return render_template('admin_dashboard.html')
        elif session['role'] == 'student':
            return render_template('student_dashboard.html')
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/create_exam', methods=['GET', 'POST'])
def create_exam():
    if 'role' in session and session['role'] == 'admin':
        if request.method == 'POST':
            exam_name = request.form['exam_name']
            date = request.form['date']
            duration = request.form['duration']
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Insert the new exam
            cursor.execute("INSERT INTO exams (exam_name, date, duration) VALUES (%s, %s, %s)", 
                           (exam_name, date, duration))
            conn.commit()
            
            # Retrieve the exam_id of the newly created exam
            exam_id = cursor.lastrowid
            
            cursor.close()
            conn.close()
            
            flash('Exam created successfully! Now, add questions to the exam.', 'success')
            # Redirect to the add_question page for the newly created exam
            return redirect(url_for('add_question', exam_id=exam_id))
        
        return render_template('create_exam.html')
    else:
        return redirect(url_for('login'))


@app.route('/add_question/<int:exam_id>', methods=['GET', 'POST'])
def add_question(exam_id):
    if request.method == 'POST':
        question_text = request.form['question_text']
        option_a = request.form['option_a']
        option_b = request.form['option_b']
        option_c = request.form['option_c']
        option_d = request.form['option_d']
        correct_option = request.form['correct_option']

        # Add the question to the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO questions (exam_id, question_text, option_a, option_b, option_c, option_d, correct_option)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (exam_id, question_text, option_a, option_b, option_c, option_d, correct_option))
        conn.commit()
        cursor.close()
        conn.close()

        # Redirect to the same page to add more questions
        return redirect(url_for('add_question', exam_id=exam_id))
    
    return render_template('add_question.html', exam_id=exam_id)



if __name__ == '__main__':
    app.run(debug=True)
