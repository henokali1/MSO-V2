from flask import Flask, render_template, flash, redirect, url_for, session, request, logging, json
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, SelectField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '@tmsqe!1321'
app.config['MYSQL_DB'] = 'MSO'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)


# Index
@app.route('/')
def index():
    return render_template('login.html')


# About
@app.route('/about')
def about():
    return render_template('about.html')

# Get current user detailes


def current_user():
    # Create Cursor
    cur = mysql.connection.cursor()

    # Get current user
    cur.execute("SELECT * FROM users WHERE email = %s",
                [session['email'].encode('utf8')])
    current_user = cur.fetchone()

    cur.close()

    first_name = current_user['first_name'].encode('utf8')
    job_title = current_user['job_title'].encode('utf8')
    department = current_user['department'].encode('utf8')
    email = current_user['email'].encode('utf8')
    return {'first_name': first_name, 'job_title': job_title, 'department': department, 'email': email}

# New MSO


@app.route('/new_mso', methods=['GET', 'POST'])
def new():
    if request.method == 'POST':
        requested_by = request.form.get('requested_by')
        section = request.form.get('section')
        department_head = request.form.get('department_head')
        location = request.form.get('location')
        description_of_service = request.form.get('description_of_service')
        actual_work_description = request.form.get('actual_work_description')
        date_started = request.form.get('date_started')
        date_completed = request.form.get('date_completed')
        work_completed_by = request.form.getlist('work_completed_by')
        work_completed_by = [x.encode('utf-8') for x in work_completed_by]
        work_completed_by = ','.join(str(e) for e in work_completed_by)

        # Create Cursor
        cur = mysql.connection.cursor()

        # Get current user
        cur.execute("SELECT first_name FROM users WHERE email = %s", [
            session['email'].encode('utf8')])

        current_user_first_name = cur.fetchone()

        # Execute
        cur.execute("INSERT INTO tsd_mso_form(posted_by, requested_by, section, department_head, location, description_of_service, actual_work_descripition, date_started, date_compleated, work_compleated_by) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (current_user_first_name['first_name'].encode('utf8'), requested_by, section, department_head, location, description_of_service, actual_work_description, date_started, date_completed, work_completed_by))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('MSO Created', 'success')

        return redirect(url_for('all_mso'))
    # Create Cursor
    cur = mysql.connection.cursor()
    # Get technicians
    cur.execute(
        "SELECT first_name, last_name FROM users WHERE job_title=%s", ['technician'])
    all_technicians = cur.fetchall()
    # Close Connection
    cur.close()

    technicians = []
    for i in all_technicians:
        technicians.append(i['first_name'].encode('utf8').capitalize() +
                           ' ' + i['last_name'].encode('utf8').capitalize())

    return render_template('new_mso.html', technicians=technicians, current_user=current_user()['first_name'], email=current_user()['email'])

# MSO's


@app.route('/all_mso')
def all_mso():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get MSO's
    result = cur.execute("SELECT * FROM tsd_mso_form ORDER BY id DESC")

    msos = cur.fetchall()

    if result > 0:
        return render_template('all_mso.html', msos=msos, current_user=current_user()['first_name'], email=current_user()['email'])
    else:
        msg = 'No MSO\'s Found'
        return render_template('all_mso', msg=msg, current_user=current_user()['first_name'], email=current_user()['email'])
    # Close db connection
    cur.close()


# Single MSO
@app.route('/mso/<string:id>/')
def mso(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get MSO
    cur.execute("SELECT * FROM tsd_mso_form WHERE id = %s", [id])

    mso = cur.fetchone()

    return render_template('mso.html', mso=mso, current_user=current_user()['first_name'], email=current_user()['email'])

# Articles


@app.route('/articles')
def articles():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html', msg=msg)
    # Close connection
    cur.close()


# Single Article
@app.route('/article/<string:id>/')
def article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article
    cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    return render_template('article.html', article=article)


# Register Form Class
class RegisterForm(Form):
    first_name = StringField('First Name', [validators.Length(min=1, max=50)])
    last_name = StringField('Last Name', [validators.Length(min=1, max=50)])
    airport_id = StringField('Airport ID Number', [validators.Length(min=1)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    job_title = SelectField(u'Job Title', choices=[('', ''), ('department_head', 'Department Head'), (
        'supervisor', 'Supervisor'), ('technician', 'Technician')])
    department = SelectField(u'Department', choices=[(
        '', ''), ('COMNAV', 'COMNAV'), ('OTHER', 'OTHER')])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        first_name = form.first_name.data
        last_name = form.last_name.data
        airport_id = form.airport_id.data
        email = form.email.data
        job_title = form.job_title.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(first_name, last_name, airport_id, email, job_title, password) VALUES(%s, %s, %s, %s, %s, %s)",
                    (first_name, last_name, airport_id, email, job_title, password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        email = request.form['email']
        password_candidate = request.form['password']
        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by email
        result = cur.execute(
            "SELECT * FROM users WHERE email = %s", [email])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['email'] = email

                flash('You are now logged in', 'success')
                if current_user()['department'] == 'OTHER':
                    return redirect(url_for('mso_request'))
                elif (current_user()['job_title'] == 'supervisor') or (current_user()['job_title'] == 'department_head'):
                    return redirect(url_for('approve'))
                else:
                    return redirect(url_for('all_mso'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'User not found'
            return render_template('login.html', error=error)
    return render_template('login.html')

# Check if user logged in


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout


@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# Dashboard


@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    # cur = mysql.connection.cursor()

    # # Get articles
    # result = cur.execute("SELECT * FROM articles")

    # articles = cur.fetchall()

    # if result > 0:
    #     return render_template('dashboard.html', articles=articles)
    # else:
    #     msg = 'No Articles Found'
    #     return render_template('dashboard.html', msg=msg)
    # # Close connection
    # cur.close()
    return render_template('dashboard.html')


# Article Form Class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])


# Add Article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)",
                    (title, body, session['email']))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('Article Created', 'success')

        return redirect(url_for('all_mso'))

    return render_template('add_article.html', form=form)

# Print MSO with the old(paper based) template.


@app.route('/mso_print')
def mso_print():
    return render_template('mso_print.html')

# Approve MSO


@app.route('/approve')
@is_logged_in
def approve():
    if (current_user()['job_title'] == 'department_head'):
        # Create cursor
        cur = mysql.connection.cursor()

        # Get MSO's
        cur.execute(
            "SELECT * FROM tsd_mso_form WHERE tsm_approval IS NULL ORDER BY id DESC")

        msos = cur.fetchall()

        cur.close()
        return render_template('approve.html', msos=msos, current_user=current_user()['first_name'], email=current_user()['email'])
    elif (current_user()['job_title'] == 'supervisor'):
        # Create cursor
        cur = mysql.connection.cursor()

        # Get MSO's
        cur.execute(
            "SELECT * FROM tsd_mso_form WHERE supervisor_approval IS NULL ORDER BY id DESC")

        msos = cur.fetchall()

        cur.close()
        return render_template('approve.html', msos=msos, current_user=current_user()['first_name'], email=current_user()['email'])
    else:
        msg = 'Only Department Heades or Supervisor\'s can approve MSO\'s'
        return render_template('not_authorized.html', msg=msg, current_user=current_user()['first_name'], email=current_user()['email'])


# Approve MSO through AJAX request.
@app.route('/approve_mso/<string:id>')
def approve_mso(id):
    id = id.replace('MSO-', '')
    if (current_user()['job_title'] == 'department_head'):
        # Create cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute(
            "UPDATE tsd_mso_form SET tsm_approval=%s, tsm_approval_date=CURRENT_TIMESTAMP WHERE id=%s", (1, id))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()
        return 'nothing'
    elif (current_user()['job_title'] == 'supervisor'):
        # Create cursor
        cur = mysql.connection.cursor()

        # Update
        cur.execute(
            "UPDATE tsd_mso_form SET supervisor_approval=%s, supervisor_approval_date=CURRENT_TIMESTAMP WHERE id=%s", (1, id))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()
        return 'nothing'

    else:
        pass

    print "Ajax is called id = " + id
    return "nothing"

# Edit MSO
@app.route('/mso/edit/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_mso(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get who requested this MSO and the requester's email
    cur.execute(
        "SELECT requested_by_other_department FROM tsd_mso_form WHERE id = %s", [id])

    requested_by_other_department = cur.fetchone()[
        'requested_by_other_department']

    cur.execute("SELECT posted_by FROM tsd_mso_form WHERE id = %s", [id])

    posted_by = cur.fetchone()['posted_by']

    if requested_by_other_department:
        if request.method == 'POST':
            # Get previous user for this MSO
            cur.execute(
                "SELECT posted_by FROM tsd_mso_form WHERE id = %s", [id])

            section = request.form.get('section')
            actual_work_description = request.form.get(
                'actual_work_description')

            date_started = request.form.get('date_started')
            date_completed = request.form.get('date_completed')
            work_completed_by = request.form.getlist('work_completed_by')
            work_completed_by = [x.encode('utf-8') for x in work_completed_by]
            work_completed_by = ','.join(str(e) for e in work_completed_by)

            # Create Cursor
            cur = mysql.connection.cursor()

            # Execute
            cur.execute("UPDATE tsd_mso_form SET work_compleated_by=%s, date_compleated=%s, date_started=%s,actual_work_descripition=%s, section=%s WHERE id=%s",
                        (work_completed_by, date_completed, date_started, actual_work_description, section, id))

            # Commit to DB
            mysql.connection.commit()

            # Close connection
            cur.close()

            flash('MSO Compleated', 'success')

            return redirect(url_for('all_mso'))

        cur.execute("SELECT * FROM tsd_mso_form WHERE id = %s", [id])
        # Get MSO
        mso = cur.fetchone()
        # Get technicians
        cur.execute(
            "SELECT first_name, last_name FROM users WHERE job_title=%s", ['technician'])
        all_technicians = cur.fetchall()
        # Close Connection
        cur.close()

        technicians = []
        for i in all_technicians:

            technicians.append(i['first_name'].encode('utf8').capitalize(
            ) + ' ' + i['last_name'].encode('utf8').capitalize())

        mso['work_compleated_by'] = ''
        return render_template('edit_mso.html', mso=mso, technicians=technicians)

    elif current_user()['first_name'] == posted_by:
        if request.method == 'POST':
            # Get previous user for this MSO
            cur.execute(
                "SELECT posted_by FROM tsd_mso_form WHERE id = %s", [id])

            requested_by = request.form.get('requested_by')
            section = request.form.get('section')
            department_head = request.form.get('department_head')
            location = request.form.get('location')
            description_of_service = request.form.get('description_of_service')
            actual_work_description = request.form.get(
                'actual_work_description')
            date_started = request.form.get('date_started')
            date_completed = request.form.get('date_completed')
            work_completed_by = request.form.getlist('work_completed_by')
            work_completed_by = [x.encode('utf-8') for x in work_completed_by]
            work_completed_by = ','.join(str(e) for e in work_completed_by)

            # Create Cursor
            cur = mysql.connection.cursor()

            # Execute
            cur.execute("UPDATE tsd_mso_form SET work_compleated_by=%s, date_compleated=%s, date_started=%s,actual_work_descripition=%s, description_of_service=%s, location=%s, department_head=%s, requested_by=%s, section=%s WHERE id=%s",
                        (work_completed_by, date_completed, date_started, actual_work_description, description_of_service, location, department_head, requested_by, section, id))

            # Commit to DB
            mysql.connection.commit()

            # Close connection
            cur.close()

            flash('MSO Updated', 'success')

            return redirect(url_for('all_mso'))

        else:
            cur.execute("SELECT * FROM tsd_mso_form WHERE id = %s", [id])
            # Get MSO
            mso = cur.fetchone()

            # Get technicians
            cur.execute(
                "SELECT first_name, last_name FROM users WHERE job_title=%s", ['technician'])
            all_technicians = cur.fetchall()
            # Close Connection
            cur.close()

            technicians = []
            for i in all_technicians:
                technicians.append(i['first_name'].encode('utf8').capitalize() +
                                   ' ' + i['last_name'].encode('utf8').capitalize())

            return render_template('edit_mso.html', mso=mso, technicians=technicians)
    # elif:

    else:
        msg = 'Only ' + posted_by.capitalize() + ' can edit this MSO.'
        return render_template('not_authorized.html', msg=msg, mso=mso)


# Edit Article


@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article by id
    cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()
    cur.close()
    # Get form
    form = ArticleForm(request.form)

    # Populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create Cursor
        cur = mysql.connection.cursor()
        app.logger.info(title)
        # Execute
        cur.execute(
            "UPDATE articles SET title=%s, body=%s WHERE id=%s", (title, body, id))
        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('Article Updated', 'success')

        return redirect(url_for('all_mso'))

    return render_template('edit_article.html', form=form)


# MSO Request
@app.route('/mso_request', methods=['GET', 'POST'])
def mso_request():
    if request.method == 'POST':
        requested_by = request.form.get('requested_by')
        department_head = request.form.get('department_head')
        location = request.form.get('location')
        description_of_service = request.form.get('description_of_service')

        # Create Cursor
        cur = mysql.connection.cursor()
        # Get current user
        user_email = current_user()['first_name']

        # Execute
        cur.execute("INSERT INTO tsd_mso_form(posted_by, requested_by, department_head, location, description_of_service, requested_by_other_department) VALUES(%s, %s, %s, %s, %s, %s)",
                    (user_email, requested_by, department_head, location, description_of_service, 1))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('MSO Request Successfull', 'success')

        return redirect(url_for('mso_request'))

    return render_template('mso_request.html', current_user=current_user()['first_name'], email=current_user()['email'])

# Delete MSO


@app.route('/mso/delete/<string:id>', methods=['GET', 'POST'])
def delete_mso(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get MSO by id
    cur.execute("SELECT * FROM tsd_mso_form WHERE id = %s", [id])
    posted_by = cur.fetchone()['posted_by']
    if current_user()['first_name'] == posted_by:
        # Execute
        cur.execute("DELETE FROM tsd_mso_form WHERE id = %s", [id])

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()
        flash('Article Deleted', 'success')
        return redirect(url_for('all_mso'))
    else:
        msg = 'Only ' + posted_by.capitalize() + ' can delete this MSO.'
        return render_template('not_authorized.html', msg=msg)


# Delete Article


@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM articles WHERE id = %s", [id])

    # Commit to DB
    mysql.connection.commit()

    # Close connection
    cur.close()

    flash('Article Deleted', 'success')

    return redirect(url_for('all_mso'))


if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug=True)
