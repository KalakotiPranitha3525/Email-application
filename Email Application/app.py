# app.py

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import smtplib
from email.message import EmailMessage
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mail.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

# Define SMTP settings model
class SMTPSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    smtp_server = db.Column(db.String(100), nullable=False)
    port = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(80), nullable=False)

# Define Email model
class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    body = db.Column(db.Text, nullable=False)

# Home page
@app.route('/')
def home():
    return render_template('index.html')

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)
        return render_template('dashboard.html', user=user)
    else:
        return redirect(url_for('login'))

# SMTP settings page
@app.route('/smtp-settings', methods=['GET', 'POST'])
def smtp_settings():
    if request.method == 'POST':
        user_id = session['user_id']
        smtp_server = request.form['smtp_server']
        port = request.form['port']
        username = request.form['username']
        password = request.form['password']
        smtp_settings = SMTPSettings(user_id=user_id, smtp_server=smtp_server, port=port, username=username, password=password)
        db.session.add(smtp_settings)
        db.session.commit()
        flash('SMTP settings saved successfully', 'success')
    return render_template('smtp_settings.html')

# Send email
@app.route('/send-email', methods=['GET', 'POST'])
def send_email():
    if request.method == 'POST':
        user_id = session['user_id']
        recipient = request.form['recipient']
        subject = request.form['subject']
        body = request.form['body']
        # Retrieve SMTP settings
        smtp_settings = SMTPSettings.query.filter_by(user_id=user_id).first()
        if smtp_settings:
            try:
                msg = EmailMessage()
                msg['From'] = smtp_settings.username
                msg['To'] = recipient
                msg['Subject'] = subject
                msg.set_content(body)
                with smtplib.SMTP(smtp_settings.smtp_server, smtp_settings.port) as server:
                    server.starttls()
                    server.login(smtp_settings.username, smtp_settings.password)
                    server.send_message(msg)
                # Save email to database
                email = Email(user_id=user_id, recipient=recipient, subject=subject, body=body)
                db.session.add(email)
                db.session.commit()
                flash('Email sent successfully', 'success')
            except Exception as e:
                flash('Failed to send email: ' + str(e), 'error')
        else:
            flash('SMTP settings not found', 'error')
    return render_template('send_email.html')

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
