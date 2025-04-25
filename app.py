from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

# Cấu hình thư mục lưu ảnh
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads', 'pets')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Trang form tải ảnh
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files.get('pet_image')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return f'Đã tải lên ảnh: {filename}'
        return 'File không hợp lệ hoặc không chọn ảnh!'
    return render_template('upload_pet_image.html')

if __name__ == '__main__':
    app.run(debug=True)


app.secret_key = 'tuvavinh'  
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///petcare.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ======== Model User =========
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.Integer, default=2)  # 1 = admin, 2 = user thường

# ======== Model Pet =========
class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    owner = db.relationship('User', backref=db.backref('pets', lazy=True))

# ======== Routes =========
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm']

        if password != confirm:
            flash('Mật khẩu xác nhận không khớp.', 'error')
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email đã tồn tại.', 'error')
            return redirect(url_for('register'))

        role = 1 if email == "admin@example.com" else 2
        new_user = User(fullname=fullname, email=email, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()

        flash('Đăng ký thành công. Hãy đăng nhập!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            session['user_id'] = user.id
            session['fullname'] = user.fullname
            session['role'] = user.role
            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Sai email hoặc mật khẩu.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Bạn cần đăng nhập để tiếp tục.', 'error')
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Đã đăng xuất.', 'info')
    return redirect(url_for('home'))

# Xem, thêm thú cưng
@app.route('/pets', methods=['GET', 'POST'])
def pets():
    if 'user_id' not in session:
        flash('Bạn cần đăng nhập.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        pet_type = request.form['type']
        age = int(request.form['age'])

        new_pet = Pet(name=name, type=pet_type, age=age, user_id=session['user_id'])
        db.session.add(new_pet)
        db.session.commit()
        flash('Thêm thú cưng thành công!', 'success')
        return redirect(url_for('pets'))

    pet_list = Pet.query.all()
    return render_template('pets.html', pets=pet_list, role=session.get('role', 2))

# Sửa thú cưng
@app.route('/pets/edit/<int:pet_id>', methods=['GET', 'POST'])
def edit_pet(pet_id):
    if 'user_id' not in session:
        flash('Bạn cần đăng nhập.', 'error')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if user.role != 1:
        flash('Bạn không có quyền chỉnh sửa thú cưng.', 'error')
        return redirect(url_for('pets'))

    pet = Pet.query.get_or_404(pet_id)

    if request.method == 'POST':
        pet.name = request.form['name']
        pet.type = request.form['type']
        pet.age = int(request.form['age'])

        db.session.commit()
        flash('Cập nhật thành công!', 'success')
        return redirect(url_for('pets'))

    return render_template('edit_pet.html', pet=pet)

# Xóa thú cưng
@app.route('/pets/delete/<int:pet_id>', methods=['POST'])
def delete_pet(pet_id):
    if 'user_id' not in session:
        flash('Bạn cần đăng nhập.', 'error')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if user.role != 1:
        flash('Bạn không có quyền xóa thú cưng.', 'error')
        return redirect(url_for('pets'))

    pet = Pet.query.get_or_404(pet_id)
    db.session.delete(pet)
    db.session.commit()
    flash('Đã xóa thú cưng.', 'info')
    return redirect(url_for('pets'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
