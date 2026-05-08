from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt
import datetime

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'your_secret_key'

# Real data with updated cover images
users = []
books = [
    {"id": 1, "title": "Data Structures and Algorithms", "author": "Robert Lafore", "category": "Computer Science", "coverImage": "https://files.manuscdn.com/user_upload_by_module/session_file/310419663028403965/PqffhqUNgjHejxnz.jpg"},
    {"id": 2, "title": "Introduction to Machine Learning", "author": "Ethem Alpaydin", "category": "AI & ML", "coverImage": "https://files.manuscdn.com/user_upload_by_module/session_file/310419663028403965/eoLEdRasCbfdJKLl.jpg"},
    {"id": 3, "title": "Quantum Physics for Beginners", "author": "Michael Brooks", "category": "Physics", "coverImage": "https://files.manuscdn.com/user_upload_by_module/session_file/310419663028403965/iOMBavLDamQHnvjI.jpg"},
    {"id": 4, "title": "Modern Web Development", "author": "Kyle Simpson", "category": "Web Development", "coverImage": "https://via.placeholder.com/150x200?text=Modern+Web+Dev"},
    {"id": 5, "title": "Clean Code", "author": "Robert C. Martin", "category": "Computer Science", "coverImage": "https://files.manuscdn.com/user_upload_by_module/session_file/310419663028403965/dsotFHpbWmlVqoqE.jpg"},
    {"id": 6, "title": "Deep Learning Illustrated", "author": "Jon Krohn", "category": "AI & ML", "coverImage": "https://files.manuscdn.com/user_upload_by_module/session_file/310419663028403965/gDhfxfjkfhEAEtxi.jpg"},
    {"id": 7, "title": "Astrophysics for People in a Hurry", "author": "Neil deGrasse Tyson", "category": "Physics", "coverImage": "https://files.manuscdn.com/user_upload_by_module/session_file/310419663028403965/mmvxMboUMISXuGjJ.jpg"},
    {"id": 8, "title": "Eloquent JavaScript", "author": "Marijn Haverbeke", "category": "Web Development", "coverImage": "https://files.manuscdn.com/user_upload_by_module/session_file/310419663028403965/WiMnFrSmEskQSHZG.jpg"},
    {"id": 9, "title": "Computer Networking: A Top-Down Approach", "author": "James Kurose", "category": "Computer Science", "coverImage": "https://files.manuscdn.com/user_upload_by_module/session_file/310419663028403965/CssZayVhRZoBJwDx.jpg"},
    {"id": 10, "title": "Pattern Recognition and Machine Learning", "author": "Christopher Bishop", "category": "AI & ML", "coverImage": "https://files.manuscdn.com/user_upload_by_module/session_file/310419663028403965/kMvUeLTCYVkQolhH.jpg"},
    {"id": 11, "title": "The Feynman Lectures on Physics", "author": "Richard Feynman", "category": "Physics", "coverImage": "https://files.manuscdn.com/user_upload_by_module/session_file/310419663028403965/TyhOYhQTgOKqnLge.jpg"},
    {"id": 12, "title": "HTML and CSS: Design and Build Websites", "author": "Jon Duckett", "category": "Web Development", "coverImage": "https://files.manuscdn.com/user_upload_by_module/session_file/310419663028403965/XKdjouKymFusvTtC.jpg"},
    {"id": 13, "title": "Operating System Concepts", "author": "Abraham Silberschatz", "category": "Computer Science", "coverImage": "https://files.manuscdn.com/user_upload_by_module/session_file/310419663028403965/WBMlpqOYTIMSuBIf.jpg"},
    {"id": 14, "title": "Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow", "author": "Aurélien Géron", "category": "AI & ML", "coverImage": "https://files.manuscdn.com/user_upload_by_module/session_file/310419663028403965/jQTiaSmkjyzajFZA.jpg"},
    {"id": 15, "title": "Seven Brief Lessons on Physics", "author": "Carlo Rovelli", "category": "Physics", "coverImage": "https://files.manuscdn.com/user_upload_by_module/session_file/310419663028403965/WLxnLQEvRgjrquYy.jpg"}
]

events = [
    {"id": 1, "title": "Research Paper Writing Workshop", "description": "Learn effective strategies for writing academic research papers.", "date": "2026-04-15", "time": "14:00 - 16:00", "location": "Main Library, Room B12"},
    {"id": 2, "title": "Digital Resources Orientation", "description": "Tour of our digital databases, e-books, and research tools.", "date": "2026-04-20", "time": "10:00 - 11:30", "location": "Library Computer Lab"},
    {"id": 3, "title": "Book Club: Classic Literature", "description": "Monthly discussion on selected classic novels. All are welcome!", "date": "2026-05-01", "time": "16:00 - 17:30", "location": "Library Reading Room"}
]

favorites = {}

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    users.append(data)
    return jsonify({"message": "User registered successfully"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = next((u for u in users if u['email'] == data['email'] and u['password'] == data['password']), None)
    if user:
        token = jwt.encode({'email': user['email'], 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)}, app.config['SECRET_KEY'])
        return jsonify({"token": token})
    return jsonify({"message": "Invalid credentials"}), 401

@app.route('/api/user/profile', methods=['GET'])
def profile():
    token = request.headers.get('Authorization').split()[1]
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        user = next((u for u in users if u['email'] == data['email']), None)
        return jsonify(user)
    except:
        return jsonify({"message": "Invalid token"}), 401

@app.route('/api/books', methods=['GET'])
def get_books():
    search = request.args.get('search', '').lower()
    category = request.args.get('category', 'All')
    filtered_books = [b for b in books if (category == 'All' or b['category'] == category) and (search in b['title'].lower() or search in b['author'].lower())]
    return jsonify(filtered_books)

@app.route('/api/events', methods=['GET'])
def get_events():
    return jsonify(events)

@app.route('/api/user/favorites', methods=['GET', 'POST'])
def handle_favorites():
    token = request.headers.get('Authorization').split()[1]
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        email = data['email']
        if request.method == 'POST':
            book_id = request.json.get('bookId')
            if email not in favorites:
                favorites[email] = []
            if book_id not in favorites[email]:
                favorites[email].append(book_id)
            return jsonify({"message": "Added to favorites"})
        else:
            user_favs = favorites.get(email, [])
            fav_books = [b for b in books if b['id'] in user_favs]
            return jsonify(fav_books)
    except:
        return jsonify({"message": "Invalid token"}), 401

@app.route('/api/complaints', methods=['POST'])
def complaints():
    return jsonify({"message": "Complaint received"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
