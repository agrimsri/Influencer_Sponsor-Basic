from flask import Blueprint,request,flash,redirect,render_template,url_for
from .models import db, User, Sponsor,Influencer
from flask_login import login_required, current_user,login_user,logout_user
from werkzeug.security import generate_password_hash,check_password_hash


auth = Blueprint('auth', __name__)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out', category='success')
    return redirect(url_for('views.home'))

@auth.route('/signup_sponsor', methods=['GET','POST'])
def signup_sponsor():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        industry = request.form.get('industry')
        budget = request.form.get('budget')
        password = request.form.get('password') 
        confirm_password = request.form.get('confirm_password')
        
        user = User.query.filter_by(email = email).first()
        if user:
            flash('User already exists',category='error')
        elif password != confirm_password:
            flash('Confirm password should match password',category='error')
        else:
            new_user = User(email = email, password = generate_password_hash(password,method='pbkdf2:sha256'), role = 'sponsor')
            new_sponsor = Sponsor(name=name, industry=industry, budget=budget)
            new_sponsor.user = new_user
            db.session.add(new_user)
            db.session.add(new_sponsor)
            db.session.commit()
            
            login_user(new_user, remember=True)
            
            flash('Account created successfully', category='success')
            return redirect(url_for('views.sponsor_dashboard'))
            
    return render_template('signup.html', user_type = 'sponsor', user = current_user)



@auth.route('/signup_influencer', methods=['GET','POST'])
def signup_influencer():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        category = request.form.get('category')
        niche = request.form.get('niche')
        reach = request.form.get('reach')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        user = User.query.filter_by(email = email).first()
        if user:
            flash('User already exists',category='error')
        elif password != confirm_password:
            flash('Confirm password should match password',category='error')
        else:
            new_user = User(email = email, password = generate_password_hash(password,method='pbkdf2:sha256'), role = 'influencer')
            new_influencer = Influencer(name = name, category = category, niche = niche, reach= reach)
            new_influencer.user = new_user
            db.session.add(new_user)
            db.session.add(new_influencer)
            db.session.commit()
            
            login_user(new_user, remember=True)
            
            flash('Account created successfully', category='success')
            return redirect(url_for('views.influencer_dashboard'))
            
    return render_template('signup.html',user = current_user, user_type = 'influencer')

@auth.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email = email).first()
        if user.role == 'admin':
            if password == '123456789':
                login_user(user, remember=True)
                flash('Logged in successfully', category='success')
            else:
                flash('Incorrect password', category='error')
            return redirect(url_for('views.admin_dashboard'))
        if user:
            if user.flagged == 'True':
                flash('Your account has been flagged. Please contact admin', category='error')
            elif check_password_hash(user.password, password):
                login_user(user, remember=True)
                flash('Logged in successfully', category='success')
                if user.role == 'sponsor':
                    return redirect(url_for('views.sponsor_dashboard'))
                elif user.role == 'influencer':
                    return redirect(url_for('views.influencer_dashboard'))
                elif user.role == 'admin':
                    return redirect(url_for('views.admin_dashboard'))
            else:
                flash('Incorrect password', category='error')
        else:
            flash('User does not exist, Signup now', category='error')
    return render_template('login.html',user = current_user)
