from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import jwt
import datetime
from functools import wraps

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'your_secret_key'

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password',
    'database': 'rst_library'
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email = %s", (data['email'],))
            current_user = cursor.fetchone()
            cursor.close()
            conn.close()
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    conn = get_db_connection()
    if not conn: return jsonify({"message": "DB Connection Error"}), 500
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (fullName, email, studentId, password) VALUES (%s, %s, %s, %s)",
                       (data['fullName'], data['email'], data['studentId'], data['password']))
        conn.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except Error as e:
        return jsonify({"message": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    conn = get_db_connection()
    if not conn: return jsonify({"message": "DB Connection Error"}), 500
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (data['email'], data['password']))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if user:
        token = jwt.encode({'email': user['email'], 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)}, app.config['SECRET_KEY'])
        return jsonify({"token": token})
    return jsonify({"message": "Invalid credentials"}), 401

@app.route('/api/books', methods=['GET'])
def get_books():
    search = request.args.get('search', '').lower()
    category = request.args.get('category', 'All')
    
    conn = get_db_connection()
    if not conn: return jsonify([])
    cursor = conn.cursor(dictionary=True)
    
    query = "SELECT * FROM books WHERE 1=1"
    params = []
    
    if category != 'All':
        query += " AND category = %s"
        params.append(category)
    
    if search:
        query += " AND (LOWER(title) LIKE %s OR LOWER(author) LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])
        
    cursor.execute(query, tuple(params))
    books = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(books)

@app.route('/api/events', methods=['GET'])
def get_events():
    conn = get_db_connection()
    if not conn: return jsonify([])
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM events ORDER BY date ASC")
    events = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(events)

@app.route('/api/user/favorites', methods=['GET', 'POST'])
@token_required
def handle_favorites(current_user):
    conn = get_db_connection()
    if not conn: return jsonify({"message": "DB Error"}), 500
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        book_id = request.json.get('bookId')
        try:
            cursor.execute("INSERT IGNORE INTO user_favorites (user_id, book_id) VALUES (%s, %s)", (current_user['id'], book_id))
            conn.commit()
            return jsonify({"message": "Added to favorites"})
        except Error as e:
            return jsonify({"message": str(e)}), 400
    else:
        cursor.execute("""
            SELECT b.* FROM books b 
            JOIN user_favorites uf ON b.id = uf.book_id 
            WHERE uf.user_id = %s
        """, (current_user['id'],))
        fav_books = cursor.fetchall()
        return jsonify(fav_books)
    
    cursor.close()
    conn.close()

@app.route('/api/complaints', methods=['POST'])
@token_required
def complaints(current_user):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO complaints (issueType, message, userId) VALUES (%s, %s, %s)",
                   (data['issueType'], data['message'], current_user['id']))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Complaint received"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
