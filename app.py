from flask import Flask,request, jsonify
import time
from models import User, db
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db.init_app(app)

MAX_RETRIES = 3
RETRY_DELAY = 0.5

# GET /users
# Return list of users

@app.route('/users', methods=['GET'])
def get_users():
    for attempt in range(MAX_RETRIES):
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 1, type=int)
            pagination = User.query.paginate(page=page, per_page=per_page, error_out=False)
            users = pagination.items
            return jsonify({
                'users': [user.serialize() for user in users],
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': pagination.page
            }), 200
        except SQLAlchemyError:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                return jsonify({'error': 'Database error'}), 500
            

# GET /users/:id
# Return specific user based on id

@app.route('/users/<int:id>', methods=['GET']) 
def get_user(id):
    for attempt in range(MAX_RETRIES):
        try:
            user = User.query.filter_by(id=id).first()
            if not user:
                return jsonify({'error': 'User not found'}), 404
            return jsonify(user.serialize()), 200
        except SQLAlchemyError:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                return jsonify({'error': 'Database error'}), 500

# POST /users
# Create new user

@app.route('/users', methods=['POST'])
def create_user():
    for attempt in range(MAX_RETRIES):
        try:
            data = request.get_json()
            if not data or 'username' not in data or 'email' not in data:
                return jsonify({'error': 'Missing username or email'}), 400
            username = data['username']
            email = data['email']
            user = User(username=username, email=email)
            db.session.add(user)
            db.session.commit()
            return jsonify(user.serialize()), 201
        except SQLAlchemyError:
            db.session.rollback()
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                return jsonify({'error': 'Database error'}), 500

# PUT /users/:id
# Update user based on id

@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    for attempt in range(MAX_RETRIES):
        try:
            user = User.query.filter_by(id=id).first()
            if not user:
                return jsonify({'error': 'User not found'}), 404
            data = request.get_json()
            if not data or 'username' not in data or 'email' not in data:
                return jsonify({'error': 'Missing username or email'}), 400
            user.username = data['username']
            user.email = data['email']
            db.session.commit()
            return jsonify(user.serialize()), 200
        except SQLAlchemyError:
            db.session.rollback()
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                return jsonify({'error': 'Database error'}), 500

# DELETE /users/:id
# Delete user

@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    for attempt in range(MAX_RETRIES):
        try:
            user = User.query.filter_by(id=id).first()
            if not user:
                return jsonify({'error': 'User not found'}), 404
            db.session.delete(user)
            db.session.commit()
            return jsonify({'message': 'User deleted'}), 200
        except SQLAlchemyError:
            db.session.rollback()
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                return jsonify({'error': 'Database error'}), 500

# Run the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5700)
