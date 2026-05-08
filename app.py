from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import jwt
import datetime
import os

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'your_secret_key_change_in_production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rst_library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==================== Database Models ====================

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    fullName = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    studentId = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    memberSince = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    coverImage = db.Column(db.String(255), default='https://via.placeholder.com/150x200?text=No+Cover')
    addedDate = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

# Association table for favorites
user_favorites = db.Table('user_favorites',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('book_id', db.Integer, db.ForeignKey('books.id'), primary_key=True)
)

class Complaint(db.Model):
    __tablename__ = 'complaints'
    id = db.Column(db.Integer, primary_key=True)
    issueType = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    userId = db.Column(db.Integer, db.ForeignKey('users.id'))
    createdAt = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# ==================== API Routes ====================

@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.json
        
        # Check if user already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({"message": "البريد الإلكتروني مستخدم بالفعل"}), 400
        
        if User.query.filter_by(studentId=data.get('studentId')).first():
            return jsonify({"message": "رقم الطالب مستخدم بالفعل"}), 400
        
        new_user = User(
            fullName=data['fullName'],
            email=data['email'],
            studentId=data.get('studentId', ''),
            password=data['password']
        )
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({"message": "تم التسجيل بنجاح"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "خطأ في التسجيل", "error": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Login user and return JWT token"""
    try:
        data = request.json
        user = User.query.filter_by(email=data['email'], password=data['password']).first()
        
        if user:
            token = jwt.encode({
                'email': user.email,
                'userId': user.id,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, app.config['SECRET_KEY'], algorithm="HS256")
            return jsonify({"token": token})
        
        return jsonify({"message": "بيانات دخول غير صحيحة"}), 401
    except Exception as e:
        return jsonify({"message": "خطأ في تسجيل الدخول", "error": str(e)}), 500

@app.route('/api/user/profile', methods=['GET'])
def profile():
    """Get user profile"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"message": "رمز مفقود"}), 401
        
        token = auth_header.split()[1]
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        user = User.query.filter_by(email=data['email']).first()
        
        if not user:
            return jsonify({"message": "المستخدم غير موجود"}), 404
        
        return jsonify({
            "id": user.id,
            "fullName": user.fullName,
            "email": user.email,
            "studentId": user.studentId,
            "memberSince": user.memberSince.strftime('%Y-%m-%d')
        })
    except Exception as e:
        return jsonify({"message": "رمز غير صحيح", "error": str(e)}), 401

@app.route('/api/books', methods=['GET'])
def get_books():
    """Get books with optional search and category filter"""
    try:
        search = request.args.get('search', '').lower()
        category = request.args.get('category', 'All')
        
        query = Book.query
        
        if category != 'All':
            query = query.filter_by(category=category)
        
        if search:
            query = query.filter(
                (Book.title.ilike(f'%{search}%')) | 
                (Book.author.ilike(f'%{search}%'))
            )
        
        books_list = query.all()
        
        return jsonify([{
            "id": b.id,
            "title": b.title,
            "author": b.author,
            "category": b.category,
            "description": b.description,
            "coverImage": b.coverImage
        } for b in books_list])
    except Exception as e:
        return jsonify({"message": "خطأ في جلب الكتب", "error": str(e)}), 500

@app.route('/api/events', methods=['GET'])
def get_events():
    """Get all events"""
    try:
        events_list = Event.query.all()
        
        return jsonify([{
            "id": e.id,
            "title": e.title,
            "description": e.description,
            "date": e.date.strftime('%Y-%m-%d'),
            "time": e.time,
            "location": e.location
        } for e in events_list])
    except Exception as e:
        return jsonify({"message": "خطأ في جلب الفعاليات", "error": str(e)}), 500

@app.route('/api/user/favorites', methods=['GET', 'POST'])
def handle_favorites():
    """Get or add favorite books"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"message": "رمز مفقود"}), 401
        
        token = auth_header.split()[1]
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        user = User.query.filter_by(email=data['email']).first()
        
        if not user:
            return jsonify({"message": "المستخدم غير موجود"}), 404
        
        if request.method == 'POST':
            book_id = request.json.get('bookId')
            book = Book.query.get(book_id)
            
            if not book:
                return jsonify({"message": "الكتاب غير موجود"}), 404
            
            # Check if already in favorites
            existing = db.session.query(user_favorites).filter(
                user_favorites.c.user_id == user.id,
                user_favorites.c.book_id == book.id
            ).first()
            
            if not existing:
                stmt = user_favorites.insert().values(user_id=user.id, book_id=book.id)
                db.session.execute(stmt)
                db.session.commit()
            
            return jsonify({"message": "تمت الإضافة للمفضلة"})
        else:
            # GET: Return favorite books
            fav_books = db.session.query(Book).join(
                user_favorites,
                user_favorites.c.book_id == Book.id
            ).filter(user_favorites.c.user_id == user.id).all()
            
            return jsonify([{
                "id": b.id,
                "title": b.title,
                "author": b.author,
                "category": b.category,
                "coverImage": b.coverImage
            } for b in fav_books])
    except Exception as e:
        return jsonify({"message": "خطأ في معالجة المفضلة", "error": str(e)}), 401

@app.route('/api/complaints', methods=['POST'])
def complaints():
    """Submit a complaint"""
    try:
        data = request.json
        auth_header = request.headers.get('Authorization')
        user_id = None
        
        if auth_header:
            try:
                token = auth_header.split()[1]
                decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
                user = User.query.filter_by(email=decoded['email']).first()
                if user:
                    user_id = user.id
            except:
                pass
        
        new_complaint = Complaint(
            issueType=data.get('issueType'),
            message=data.get('message'),
            userId=user_id
        )
        db.session.add(new_complaint)
        db.session.commit()
        
        return jsonify({"message": "تم استقبال الشكوى بنجاح"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "خطأ في إرسال الشكوى", "error": str(e)}), 500

# ==================== Database Initialization ====================

def init_db():
    """Initialize database with sample data"""
    with app.app_context():
        db.create_all()
        
        # Check if data already exists
        if Book.query.first():
            return
        
        # Add sample books
        books_data = [
            ("Data Structures and Algorithms", "Robert Lafore", "Computer Science", "كتاب شامل عن هياكل البيانات والخوارزميات", "https://files.manuscdn.com/user_upload_by_module/session_file/310419663028403965/PqffhqUNgjHejxnz.jpg"),
            ("Introduction to Machine Learning", "Ethem Alpaydin", "AI & ML", "مقدمة شاملة للتعلم الآلي", "https://files.manuscdn.com/user_upload_by_module/session_file/310419663028403965/eoLEdRasCbfdJKLl.jpg"),
            ("Quantum Physics for Beginners", "Michael Brooks", "Physics", "شرح الفيزياء الكمية للمبتدئين", "https://files.manuscdn.com/user_upload_by_module/session_file/310419663028403965/iOMBavLDamQHnvjI.jpg"),
            ("Modern Web Development", "Kyle Simpson", "Web Development", "تطوير الويب الحديث", "https://files.manuscdn.com/user_upload_by_module/session_file/310519663621429151/UhnyibbEeXJqRBBL.jpg"),
            ("Clean Code", "Robert C. Martin", "Computer Science", "كتابة كود نظيف واحترافي", "https://files.manuscdn.com/user_upload_by_module/session_file/310419663028403965/dsotFHpbWmlVqoqE.jpg"),
            ("Deep Learning Illustrated", "Jon Krohn", "AI & ML", "التعلم العميق بالرسوم التوضيحية", "https://files.manuscdn.com/user_upload_by_module/session_file/310419663028403965/gDhfxfjkfhEAEtxi.jpg"),
            ("Astrophysics for People in a Hurry", "Neil deGrasse Tyson", "Physics", "الفيزياء الفلكية بسرعة", "https://files.manuscdn.com/user_upload_by_module/session_file/310419663028403965/mmvxMboUMISXuGjJ.jpg"),
            ("Eloquent JavaScript", "Marijn Haverbeke", "Web Development", "جافاسكريبت فعّال وجميل", "https://files.manuscdn.com/user_upload_by_module/session_file/310419663028403965/WiMnFrSmEskQSHZG.jpg"),
        ]
        
        for title, author, category, description, cover in books_data:
            book = Book(
                title=title,
                author=author,
                category=category,
                description=description,
                coverImage=cover
            )
            db.session.add(book)
        
        # Add sample events
        events_data = [
            ("Research Paper Writing Workshop", "تعلم استراتيجيات فعّالة لكتابة الأوراق البحثية", datetime.date(2026, 4, 15), "14:00 - 16:00", "Main Library, Room B12"),
            ("Digital Resources Orientation", "جولة في قواعد البيانات الرقمية والكتب الإلكترونية", datetime.date(2026, 4, 20), "10:00 - 11:30", "Library Computer Lab"),
            ("Book Club: Classic Literature", "نقاش شهري حول الأدب الكلاسيكي", datetime.date(2026, 5, 1), "16:00 - 17:30", "Library Reading Room"),
            ("Citation Management Tools", "ورشة عمل حول أدوات إدارة المراجع", datetime.date(2026, 5, 10), "13:00 - 14:30", "Online (Zoom)"),
        ]
        
        for title, description, date, time, location in events_data:
            event = Event(
                title=title,
                description=description,
                date=date,
                time=time,
                location=location
            )
            db.session.add(event)
        
        db.session.commit()
        print("✓ تم تهيئة قاعدة البيانات بنجاح")

# ==================== Main ====================

if __name__ == '__main__':
    init_db()
    print("🚀 تطبيق مكتبة RST يعمل على http://localhost:5000")
    app.run(debug=True, port=5000)
