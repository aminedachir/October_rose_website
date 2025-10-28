import re
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blood_donation.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Donor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False, unique=True)
    blood_type = db.Column(db.String(5), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Donor {self.name}>'

ADMIN_CREDENTIALS = {
    'username': 'dachir',
    'password': 'dachir@@@'
}

def validate_name(name):
    """Validate that name contains only Arabic and English letters and spaces"""
    pattern = r'^[\u0600-\u06FFa-zA-Z\s]+$'
    return bool(re.match(pattern, name.strip()))

def validate_phone(phone):
    """Validate that phone contains only numbers and optional + at start"""
    pattern = r'^\+?[0-9\s\-]+$'
    return bool(re.match(pattern, phone.strip()))

with app.app_context():
    db.create_all()
    print("✅ Database tables created successfully")

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/donate', methods=['GET', 'POST'])
def donate():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        blood_type = request.form['blood_type']
        
        if not validate_name(name):
            flash('الاسم يجب أن يحتوي على أحرف فقط (عربية أو إنجليزية)', 'error')
            return render_template('donate.html', name=name, phone=phone, blood_type=blood_type)
        
        if not validate_phone(phone):
            flash('رقم الهاتف يجب أن يحتوي على أرقام فقط', 'error')
            return render_template('donate.html', name=name, phone=phone, blood_type=blood_type)
        
        cleaned_phone = re.sub(r'[^\d+]', '', phone)
        
        existing_donor = Donor.query.filter_by(phone=cleaned_phone).first()
        if existing_donor:
            flash('رقم الهاتف مسجل مسبقاً', 'error')
            return render_template('donate.html', name=name, phone=phone, blood_type=blood_type)
        
        donor = Donor(name=name.strip(), phone=cleaned_phone, blood_type=blood_type)
        db.session.add(donor)
        db.session.commit()
        
        flash('شكراً لك على التبرع! تم تسجيل معلوماتك بنجاح', 'success')
        return redirect(url_for('donate'))
    
    return render_template('donate.html')

@app.route('/donors')
def donors_list():
    donors = Donor.query.order_by(Donor.created_at.desc()).all()
    return render_template('donors.html', donors=donors)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_CREDENTIALS['username'] and password == ADMIN_CREDENTIALS['password']:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('تم تسجيل الدخول بنجاح!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        flash('يجب تسجيل الدخول أولاً', 'error')
        return redirect(url_for('admin_login'))
    
    donors = Donor.query.order_by(Donor.created_at.desc()).all()
    total_donors = len(donors)
    
    blood_types_count = 0
    if donors:
        blood_types_set = set()
        for donor in donors:
            blood_types_set.add(donor.blood_type)
        blood_types_count = len(blood_types_set)
    
    return render_template('admin_dashboard.html', 
                         donors=donors, 
                         total_donors=total_donors,
                         blood_types_count=blood_types_count)

@app.route('/admin/delete/<int:donor_id>', methods=['POST'])
def admin_delete_donor(donor_id):
    if not session.get('admin_logged_in'):
        flash('يجب تسجيل الدخول أولاً', 'error')
        return redirect(url_for('admin_login'))
    
    donor = Donor.query.get_or_404(donor_id)
    db.session.delete(donor)
    db.session.commit()
    flash('تم حذف المتبرع بنجاح', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)