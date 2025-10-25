from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
import hashlib
import mysql.connector
from flask import render_template
from datetime import datetime, time, timedelta
from datetime import datetime, timedelta



app = Flask(__name__)
app.secret_key = 'Aries1981'


@app.template_filter('strftime')
def format_time(value, format="%I:%M %p"):
    if isinstance(value, time):
        return value.strftime(format)
    return value  


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Aries1981",
        database="student_dashboard"
    )
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

    
@app.route('/dashboard')
def dashboard():
    if 'student_number' not in session:
        return redirect(url_for('login'))

    student_number = session['student_number']
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = "SELECT student_number, name, program, year_section, status FROM student_info WHERE student_number = %s"
    cursor.execute(query, (student_number,))
    student_info = cursor.fetchone()

    conn.close()

    if student_info:
        return render_template('dashboard.html', student_info=student_info)
    else:
        return "Student information not found."


    
@app.route('/')
def home():
    if 'student_number' not in session:
        return redirect(url_for('login')) 

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

   
    cursor.execute("SELECT * FROM users WHERE student_number = %s", (session['student_number'],))
    user_info = cursor.fetchone()

    
    cursor.execute("SELECT * FROM student_info WHERE student_number = %s", (session['student_number'],))
    student_info = cursor.fetchone()

    cursor.close()
    conn.close()

    if user_info and student_info:
        return render_template('dashboard.html', user_info=user_info, student_info=student_info)
    else:
        return "User data not found!", 404  


@app.route('/student_information', methods=['GET', 'POST'])
def student_information():
    if 'student_number' not in session:
        return redirect(url_for('login')) 

    student_number = session['student_number']

    if request.method == 'POST':
        
        name = request.form['name']
        program = request.form['program']
        year_section = request.form['year_section']
        status = request.form['status']
        email = request.form['email']
        contact_number = request.form['contact_number']
        address = request.form['address']
        birthdate = request.form['birthdate']

       
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(""" 
            UPDATE student_info
            SET name = %s, program = %s, year_section = %s, status = %s,
                email = %s, contact_number = %s, address = %s, birthdate = %s
            WHERE student_number = %s
        """, (name, program, year_section, status, email, contact_number, address, birthdate, student_number))
        conn.commit()
        cursor.close()
        conn.close()

        flash("Student information updated successfully!", "success")
        return redirect(url_for('student_information'))

   
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM student_info WHERE student_number = %s", (student_number,))
    student_info = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('student_information.html', student_info=student_info)

@app.route('/manage_subjects')
def manage_subjects():
    if 'student_number' not in session:
        return redirect(url_for('login'))

    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Aries1981',
        database='student_dashboard'
    )

    cursor = conn.cursor(dictionary=True)

    # Fetch student info
    cursor.execute("SELECT * FROM student_info WHERE student_number = %s", (session['student_number'],))
    student_info = cursor.fetchone()

    # Fetch subject data
    cursor.execute("SELECT * FROM subjects WHERE student_number = %s", (session['student_number'],))
    subjects = cursor.fetchall()

    for subject in subjects:
        # Convert start and end times from timedelta to time if necessary
        if isinstance(subject['schedule_time1'], timedelta):
            subject['schedule_time1'] = (datetime.min + subject['schedule_time1']).time()

        if isinstance(subject['schedule_time2'], timedelta):
            subject['schedule_time2'] = (datetime.min + subject['schedule_time2']).time()

        if isinstance(subject.get('schedule_endtime1'), timedelta):
            subject['schedule_endtime1'] = (datetime.min + subject['schedule_endtime1']).time()

        if isinstance(subject.get('schedule_endtime2'), timedelta):
            subject['schedule_endtime2'] = (datetime.min + subject['schedule_endtime2']).time()

    cursor.close()
    conn.close()

    return render_template('manage_subjects.html', student_info=student_info, subjects=subjects)




@app.route('/edit_subject', methods=['POST'])
def edit_subject():
    try:
        data = request.get_json()
        subject_id = data['subject_id']
        subject_code = data['subject_code']
        subject_name = data['subject_name']
        instructor = data['instructor']

        schedule_day1 = data.get('schedule_day1', '')
        schedule_time1 = data.get('schedule_time1', '')
        schedule_endtime1 = data.get('schedule_endtime1', '')

        schedule_day2 = data.get('schedule_day2', '')
        schedule_time2 = data.get('schedule_time2', '')
        schedule_endtime2 = data.get('schedule_endtime2', '')

        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Aries1981',
            database='student_dashboard'
        )
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE subjects 
            SET subject_code = %s, subject_name = %s, instructor = %s,
                schedule_day1 = %s, schedule_time1 = %s, schedule_endtime1 = %s,
                schedule_day2 = %s, schedule_time2 = %s, schedule_endtime2 = %s
            WHERE subject_id = %s AND student_number = %s
        """, (
            subject_code, subject_name, instructor,
            schedule_day1, schedule_time1, schedule_endtime1,
            schedule_day2, schedule_time2, schedule_endtime2,
            subject_id, session['student_number']
        ))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'message': 'Subject updated successfully'}), 200

    except Exception as e:
        print('Failed to update subject:', e)
        return jsonify({'message': 'Failed to update subject'}), 500


    
@app.route('/delete_subject', methods=['POST'])
def delete_subject():
    subject_id = request.json.get('subject_id')
    db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Aries1981',
    'database': 'student_dashboard'
}
    if not subject_id:
        return jsonify({"message": "Subject ID is required.", "success": False})
    
    try:
       
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
    
        cursor.execute("DELETE FROM subjects WHERE subject_id = %s", (subject_id,))
        conn.commit()
        
      
        if cursor.rowcount == 0:
            return jsonify({"message": "No subject found with this ID.", "success": False})
        
        cursor.close()
        conn.close()
        
        return jsonify({"message": "Subject deleted successfully!", "success": True})
    
    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({"message": f"Failed to delete subject. Error: {e}", "success": False})



from datetime import datetime

@app.route('/add_subject', methods=['POST'])
def add_subject():
    subject_name = request.form['subject_name']
    subject_code = request.form['subject_code']
    instructor = request.form['instructor']
    schedule_day1 = request.form.get('schedule_day1')
    schedule_day2 = request.form.get('schedule_day2')
    schedule_time1 = request.form.get('schedule_time1')
    schedule_time2 = request.form.get('schedule_time2')
    schedule_endtime1 = request.form.get('schedule_endtime1')
    schedule_endtime2 = request.form.get('schedule_endtime2')

    if not all([schedule_day1, schedule_time1, schedule_endtime1, schedule_day2, schedule_time2, schedule_endtime2]):
        flash("Missing schedule information", "error")
        return redirect(url_for('manage_subjects'))

    try:
        schedule_time1 = datetime.strptime(schedule_time1, '%H:%M').time()
        schedule_time2 = datetime.strptime(schedule_time2, '%H:%M').time()
        schedule_endtime1 = datetime.strptime(schedule_endtime1, '%H:%M').time()
        schedule_endtime2 = datetime.strptime(schedule_endtime2, '%H:%M').time()
    except ValueError as e:
        flash(f"Error parsing time: {e}", "error")
        return redirect(url_for('manage_subjects'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        sql = """
            INSERT INTO subjects (
                subject_name, subject_code, instructor,
                schedule_day1, schedule_time1, schedule_endtime1,
                schedule_day2, schedule_time2, schedule_endtime2,
                student_number
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            subject_name, subject_code, instructor,
            schedule_day1, schedule_time1, schedule_endtime1,
            schedule_day2, schedule_time2, schedule_endtime2,
            session['student_number']
        )

        cursor.execute(sql, values)
        conn.commit()
        flash("Subject added successfully!", "success")
    except Exception as e:
        if "Duplicate entry" in str(e):
            flash("Subject name already exists. Please use a different name or delete the existing one first.", "error")
        else:
            flash(f"An error occurred: {e}", "error")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('manage_subjects'))

@app.route('/manage_scores', methods=['GET', 'POST'])
def manage_scores():
   
    student_number = session.get('student_number') 

    if not student_number:
       
        return redirect(url_for('login'))

  
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Aries1981',
        database='student_dashboard'
    )
    cursor = conn.cursor(dictionary=True)

   
    cursor.execute("SELECT student_number, name, program, year_section, status FROM student_info WHERE student_number = %s", (student_number,))
    student_info = cursor.fetchone() 

   
    cursor.execute("SELECT subject_id, subject_name FROM subjects")
    subjects = cursor.fetchall()

   
    cursor.execute("SELECT score_id, subject_name, score_type, score, score_type_number, exam_type FROM scores")
    scores = cursor.fetchall()

    cursor.close()
    conn.close()

   
    if request.method == 'POST':
        subject_name = request.form.get('subject_name')
        score_type = request.form.get('score_type')
        score_type_number = request.form.get('score_type_number')  
        exam_type = request.form.get('exam_type')  
        score = request.form.get('score')

       
        if score_type == 'Exam':
            score_type_number = None  

      
        try:
            insert_score_to_db(subject_name, score_type, score_type_number, exam_type, score)
            return redirect(url_for('manage_scores')) 
        except Exception as e:
            print(e)
            return "Error occurred while adding the score."

  
    return render_template('manage_scores.html', student_info=student_info, subjects=subjects, scores=scores)



def get_student_info():
   
    student = {
        "student_number": "202202001",
        "name": "Rance Gabrielle G. Siroy",
        "program": "BS Computer Science",
        "year_section": "2-2",
        "status": "Irregular"
    }
    return student

@app.route('/add_score', methods=['POST'])
def add_score():
    subject_name = request.form.get('subject_name')
    score_type = request.form.get('score_type')
    score_type_number = request.form.get('score_type_number')
    exam_type = request.form.get('exam_type')
    score = request.form.get('score')

    if score_type == 'Exam':
        score_type_number = None
    else:
        exam_type = None

    try:
        insert_score_to_db(subject_name, score_type, score_type_number, exam_type, score)
        return redirect(url_for('manage_scores'))
    except ValueError as ve:
        flash(str(ve), 'error')
        return redirect(url_for('manage_scores'))
    except Exception as e:
        flash("Error occurred while adding the score.", 'error')
        return redirect(url_for('manage_scores'))


def insert_score_to_db(subject_name, score_type, score_type_number, exam_type, score):
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Aries1981',
        database='student_dashboard'
    )
    cursor = conn.cursor()

    # Check for duplicates
    if score_type in ['Quiz', 'Activity']:
        cursor.execute("""
            SELECT * FROM scores 
            WHERE subject_name = %s AND score_type = %s AND score_type_number = %s
        """, (subject_name, score_type, score_type_number))
        existing = cursor.fetchone()
        if existing:
            raise ValueError(f"{score_type} #{score_type_number} already exists for {subject_name}.")

    elif score_type == 'Exam':
        cursor.execute("""
            SELECT * FROM scores 
            WHERE subject_name = %s AND score_type = %s AND exam_type = %s
        """, (subject_name, score_type, exam_type))
        existing = cursor.fetchone()
        if existing:
            raise ValueError(f"{exam_type} already exists for {subject_name}.")

    # Insert if no duplicate
    query = """
        INSERT INTO scores (subject_name, score_type, score_type_number, exam_type, score)
        VALUES (%s, %s, %s, %s, %s)
    """
    data = (subject_name, score_type, score_type_number, exam_type, score)

    try:
        cursor.execute(query, data)
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
        
@app.route('/edit_score', methods=['POST'])
def edit_score():
    try:
        data = request.get_json()
        score_id = data['score_id']
        subject_name = data['subject_name']
        score_type = data['score_type']
        score_type_number = data.get('score_type_number') if data['score_type'] != 'Exam' else None
        exam_type = data['exam_type']
        score = data['score']

        
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Aries1981',
            database='student_dashboard'
        )
        cursor = conn.cursor()

       
        cursor.execute("""
            UPDATE scores
            SET subject_name = %s, score_type = %s, score_type_number = %s, exam_type = %s, score = %s
            WHERE score_id = %s
        """, (subject_name, score_type, score_type_number, exam_type, score, score_id))

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({'message': 'Score updated successfully'}), 200

    except Exception as e:
        print(f'Failed to update score: {e}')
        return jsonify({'message': 'Failed to update score'}), 500
    
    
@app.route('/delete_score', methods=['POST'])
def delete_score():
    
    try:
        data = request.get_json()
        score_id = data.get('score_id')
        
        if not score_id:
            return jsonify({'success': False, 'message': 'Score ID is required'}), 400

       
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Aries1981',
            database='student_dashboard'
        )
        cursor = conn.cursor()

       
        query = "DELETE FROM scores WHERE score_id = %s"
        
       
        cursor.execute(query, (score_id,))
        conn.commit()

        if cursor.rowcount > 0:
           
            return jsonify({'success': True, 'message': 'Score deleted successfully'}), 200
        else:
          
            return jsonify({'success': False, 'message': 'Score not found'}), 404

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({'success': False, 'message': 'Error deleting score'}), 500
    finally:
       
        cursor.close()
        conn.close()
        
from flask import flash, render_template, redirect, url_for, session, request

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'student_number' in session: 
        return redirect(url_for('dashboard')) 
    
    if request.method == 'POST':
        student_number = request.form['student_number']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        query = "SELECT password FROM users WHERE student_number = %s"
        cursor.execute(query, (student_number,))
        result = cursor.fetchone()

        if result:
            db_password = result[0]

            if password == db_password:
                session['student_number'] = student_number
                return redirect(url_for('loading')) 
            else:
                flash('Invalid password. Please try again.', 'error')  # flash as 'error' category
                return redirect(url_for('login'))
        else:
            flash('Invalid student number. Please try again.', 'error')  # flash as 'error' category
            return redirect(url_for('login'))
    
    return render_template('login.html')


from flask import render_template, request, redirect, url_for
import mysql.connector

@app.route('/search_subject', methods=['GET', 'POST'])
def search_subject():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Aries1981',
        database='student_dashboard'
    )
    cursor = conn.cursor(dictionary=True, buffered=True)

   
    cursor.execute("SELECT * FROM student_info WHERE student_number = %s", (202220064,))
    student_info = cursor.fetchone()

    subject_info = None
    scores = {}

    if request.method == 'POST':
        subject_name = request.form['subject_name']

        
        cursor.execute("SELECT * FROM subjects WHERE subject_name = %s", (subject_name,))
        subject_info = cursor.fetchone()

        if subject_info:
            
            if isinstance(subject_info['schedule_time1'], timedelta):
                time_obj = (datetime.min + subject_info['schedule_time1']).time()
                subject_info['schedule_time1'] = time_obj.strftime('%I:%M %p')
            if isinstance(subject_info['schedule_time2'], timedelta):
                time_obj = (datetime.min + subject_info['schedule_time2']).time()
                subject_info['schedule_time2'] = time_obj.strftime('%I:%M %p')

            subject_id = subject_info['subject_name']

            cursor.execute("""
                SELECT score_type, score_type_number, score, exam_type
                FROM scores 
                WHERE subject_name = %s
            """, (subject_id,))
            score_records = cursor.fetchall()

            for record in score_records:
                score_type = record['score_type']
                score_type_number = record['score_type_number']
                score = record['score']
                exam_type = record['exam_type']

                if score_type not in scores:
                    scores[score_type] = {}

                if score_type == 'Exam' and exam_type:
                    scores[score_type][exam_type] = score
                else:
                    scores[score_type][score_type_number] = score

   
    cursor.execute("SELECT subject_name FROM subjects")
    subjects = cursor.fetchall()

    conn.close()

    return render_template('search_subject.html',
                           student_info=student_info,
                           subjects=subjects,
                           subject_info=subject_info,
                           scores=scores)

def get_subjects():
   
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Aries1981',
        database='student_dashboard'
    )
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT subject_name FROM subjects")
    subjects = cursor.fetchall()
    conn.close()
    return subjects


@app.route('/performance_graph')
def performance_graph():
    import mysql.connector

    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Aries1981',
        database='student_dashboard'
    )
    cursor = conn.cursor(dictionary=True)

    
    cursor.execute("SELECT score_type, exam_type, score FROM scores")
    scores = cursor.fetchall()

   
    quiz_scores = [row['score'] for row in scores if row['score_type'] == 'Quiz']
    activity_scores = [row['score'] for row in scores if row['score_type'] == 'Activity']
   
    midterm_scores = [row['score'] for row in scores if row['score_type'] == 'Exam' and row['exam_type'] == 'Midterm']
    final_scores = [row['score'] for row in scores if row['score_type'] == 'Exam' and row['exam_type'] == 'Finals']

   
    def average(score_list):
        return round(sum(score_list) / len(score_list), 2) if score_list else 0

    performance_data = [
        average(quiz_scores),
        average(activity_scores),
        average(midterm_scores),
        average(final_scores)
    ]
    labels = ['Quiz', 'Activity', 'Midterm', 'Final']

    cursor.close()
    conn.close()

    return render_template('performance_graph.html', labels=labels, performance_data=performance_data)


@app.route('/calendar')
def calendar():
    if 'student_number' not in session:
        return redirect(url_for('login'))

    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Aries1981',
        database='student_dashboard'
    )
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT subject_name, schedule_day1, schedule_day2, schedule_time1, schedule_time2 FROM subjects WHERE student_number = %s", (session['student_number'],))
    subjects = cursor.fetchall()
    cursor.close()
    conn.close()

    events = []

    for subject in subjects:
        for i in [1, 2]:  # Loop through day1/time1 and day2/time2
            day_key = f'schedule_day{i}'
            time_key = f'schedule_time{i}'

            if subject[day_key] and subject[time_key]:
                raw_time = subject[time_key]

                # Convert timedelta or string to datetime.time
                if isinstance(raw_time, timedelta):
                    total_seconds = raw_time.total_seconds()
                    hours = int(total_seconds // 3600)
                    minutes = int((total_seconds % 3600) // 60)
                    start_time_obj = datetime.strptime(f'{hours:02}:{minutes:02}', '%H:%M')
                else:
                    try:
                        start_time_obj = datetime.strptime(subject[time_key], '%H:%M')
                    except:
                        continue  # Skip invalid

                # End time = start time + 1 hour (you can customize this duration)
                end_time_obj = start_time_obj + timedelta(hours=1)

                events.append({
                    'subject_name': subject['subject_name'],
                    'day': subject[day_key],
                    'start': start_time_obj.strftime('%I:%M %p'),
                    'end': end_time_obj.strftime('%I:%M %p')
                })

    return render_template('calendar.html', events=events)



@app.route('/loading')
def loading():
   
    if 'student_number' not in session:
        return redirect(url_for('login'))
    return render_template('loading.html')


   

@app.route('/logout')
def logout():
    session.pop('student_number', None)  
    session.pop('name', None)  
    return redirect(url_for('login')) 


if __name__ == '__main__':
    app.run(debug=True)

