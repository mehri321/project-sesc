from flask import Flask, render_template, request, session, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import uuid
from datetime import datetime
from helperControllers.externalAccountCreation import *
from helperControllers.invoices import GENERATE_INVOICE, CANCEL_INVOICE

app = Flask(__name__)
app.secret_key = "students-portal-LSDKF23"

# Configure the database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students_portal.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(30), nullable=True)
    last_name = db.Column(db.String(30), nullable=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    student_id = db.Column(db.String(10), unique=True, nullable=True)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        if not self.student_id:
            self.student_id = str(uuid.uuid4()).replace('-', '')[:6].upper()

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

    def __repr__(self):
        return f'<User {self.username}>'

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    enrolled_by = db.relationship('Enrollment', back_populates='course')
    

    def __repr__(self):
        return f'<Course {self.title}>'

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(100), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course = db.relationship('Course', back_populates='enrolled_by')
    user = db.relationship('User', back_populates='enrollments')

    def __repr__(self):
        return f'<Enrollment Reference: {self.reference}, Course ID: {self.course_id}, User: {self.user.username}>'

User.enrollments = db.relationship('Enrollment', order_by=Enrollment.id, back_populates='user')


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))





@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        existing_user = User.query.filter_by(email=email).first()
        
        if existing_user is None:
            user = User(username=username, email=email, password=password)
            db.session.add(user)
            db.session.commit()
            
            try:
                lib_account_created = CREATE_LIBRARY_ACCOUNT(user.student_id)
                fin_account_created = CREATE_FINANCE_ACCOUNT(user)
            except Exception as e:
                print(f"An error occurred: {e}")
                lib_account_created = False
                fin_account_created = False

            print(f"Finance: {fin_account_created}\n Library : {lib_account_created}")
            if lib_account_created and fin_account_created:
                flash('Registration successful!', 'success')
                return redirect(url_for('login'))
            else:
                db.session.delete(user)
                db.session.commit()
                flash('Registration Failed! Could not create required accounts.', 'danger')
                return redirect(url_for('register'))
        else:
            flash('User already exists!', 'danger')
            return redirect(url_for('register'))
    return redirect('/')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password', 'danger')

    return redirect('/')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect("/")

# Home route
@app.route('/')
def home():
    return render_template("temp/home.html")

# All courses route
@app.route("/all-courses")
@login_required
def all_courses():
    courses = Course.query.all()

    data = {
        "title": "All Courses List",
        "courses":courses
    }
    return render_template("temp/courses.html", data=data)


@app.route("/enrolled-courses")
@login_required
def enrolled_courses():
    user_enrollments = Enrollment.query.filter_by(user_id=current_user.id).all()
    enrolled_courses = [enrollment.course for enrollment in user_enrollments]
    data = {
        "title": "Enrolled Courses List",
        "courses": enrolled_courses
    }
    return render_template("temp/courses.html", data=data)


@app.route('/search', methods=['GET'])
@login_required
def search_courses():
    query = request.args.get('query')
    if query:
        # Find courses where the query is in the title or description
        search = f"%{query}%"
        courses = Course.query.filter(
            (Course.title.ilike(search)) | 
            (Course.description.ilike(search))
        ).all()
    else:
        courses = []

    data = {
        "title": "Search Results",
        "courses": courses
    }
    return render_template("temp/courses.html", data=data)





@app.route("/profile", methods=['POST', 'GET'])
@login_required
def student_profile():
    if request.method == 'POST':
        first_name = request.form['f_name']
        last_name = request.form['l_name']
        email = request.form['email']
        username = request.form['username']
        
        email_exists = User.query.filter(User.email == email, User.id != current_user.id).first()

        username_exists = User.query.filter(User.username == username, User.id != current_user.id).first()

        if email_exists:
            flash("Email already in use", "danger")
        elif username_exists:
            flash("Username already in use", "danger")
        else:
            # Update the current user's information
            current_user.email = email
            current_user.username = username
            current_user.first_name = first_name
            current_user.last_name = last_name
            db.session.commit()
            flash("Your info is updated", "success")

    data = {
        "title": "Student Profile",
        "user": current_user
    }
    return render_template("temp/profile.html", data=data)


@app.route("/graduation-status")
@login_required
def graduation_status():
    student_info = get_student_info(current_user.student_id)
    
    if student_info['err']:
        flash(student_info['err'], "danger")
        return redirect(url_for('graduation_status'))  # Redirect to profile or another appropriate page

    if student_info['acc']:
        if not student_info['bal']:
            data = {
                "status": "Eligible For",
                "note": "Congratulations! You're eligible for graduation."
            }
        else:
            reason = "You have not met the graduation requirements."
            data = {
                "status": "Not Eligible",
                "note": f"{reason} Please clear your balance and fulfill all requirements to graduate."
            }
    else:
        data = {
            "status": "No Account",
            "note": "You do not have a finance account in the system. Please contact support.",
            "createAccount":True
        }
    
    return render_template("temp/graduationStatus.html", data=data)


@app.route('/course/<int:course_id>')
@login_required
def course_view(course_id):
    course = Course.query.get_or_404(course_id)
    enrollment = Enrollment.query.filter_by(course_id=course_id, user_id=current_user.id).first()
    data = {
        "course": course,
        "enrollment": enrollment
    }
    return render_template("temp/courseView.html", data=data)




@app.route("/cancel-enrollment/<int:enrollment_id>")
@login_required
def cancel_enrollment(enrollment_id):
    try:
        enrollment = Enrollment.query.get_or_404(enrollment_id)
        
        if enrollment.user_id != current_user.id:
            flash("You are not authorized to cancel this enrollment.", "danger")
            return redirect(url_for('enrolled_courses'))

        # Cancel the invoice associated with this enrollment
        invoice_cancel_result = CANCEL_INVOICE(enrollment.reference)

        if invoice_cancel_result["is_cancelled"]:
            db.session.delete(enrollment)
            db.session.commit()
            flash(invoice_cancel_result["message"], 'success')
        else:
            flash(invoice_cancel_result["message"], 'danger')

    except Exception as e:
        flash(f"An error occurred: {e}", "danger")
    
    return redirect(url_for('enrolled_courses'))



@app.route('/enroll/<int:course_id>')
@login_required
def enroll_course(course_id):
    course = Course.query.get_or_404(course_id)
    invoice_generated = GENERATE_INVOICE(course.amount, current_user.student_id)
    
    if not invoice_generated["is_created"]:
        if invoice_generated.get("invalid_student"):
            flash("Invalid student ID. Invoice not created.", "danger")
        else:
            flash("Invoice not created due to a server error.", "danger")
        return redirect(url_for("course_view", course_id=course.id))
    
    enrollment = Enrollment(
        reference=invoice_generated['reference'],
        course_id=course.id,
        user_id=current_user.id
    )
    try:
        db.session.add(enrollment)
        db.session.commit()
        flash(f'You have been enrolled in {course.title} with reference: {enrollment.reference}', 'success')
    except Exception as e:
        db.session.rollback()
        flash("An error occurred during enrollment. Please try again.", "danger")
        print(f"An error occurred: {e}")
    
    return redirect(url_for('course_view', course_id=course.id))

@app.route("/reg-finance", methods=['GET'])
@login_required
def retry_finance_account():
    try:
        account_created = CREATE_FINANCE_ACCOUNT(current_user)
        lib_account = CREATE_LIBRARY_ACCOUNT(current_user.student_id)
        if account_created:
            flash("Your finance account has been created successfully.", "success")
        else:
            flash("An error occurred while creating your finance account. Please try again later.", "danger")
    except Exception as e:
        flash("An error occurred while creating your finance account. Please try again later.", "danger")
        print(f"An error occurred: {e}")
        return redirect(url_for('graduation_status'))

    return redirect(url_for('graduation_status'))

if __name__ == '__main__':
    app.run(debug=True)