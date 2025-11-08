import hashlib
import os

from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from uuid import uuid4 as uuid
from datetime import datetime as dt, timezone as tz
from typing import Optional


DATABASE_PATH = 'pastebin.db'
COOKIE_NAME = 'PBSESSION'
TEXT_LENGTH_LIMIT = 5000
PASTE_ID_LENGTH = 8

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}'.format(os.path.join(os.getenv('DATA_DIR', '.'), DATABASE_PATH))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True)
    password_hash = db.Column(db.String(64))
    password_salt = db.Column(db.String(32), unique=True)
    session = db.relationship('Session', uselist=True, backref=db.backref('user', lazy=True))
    paste = db.relationship('Paste', uselist=True, backref=db.backref('user', lazy=True))

    @staticmethod
    def by_username(username: str) -> Optional['User']:
        return User.query.filter_by(username=username).first()


class Session(db.Model):
    id = db.Column(db.String(32), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Paste(db.Model):
    id = db.Column(db.String(PASTE_ID_LENGTH), primary_key=True)
    text = db.Column(db.String, nullable=True)
    image = db.Column(db.String, nullable=True)
    size = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=dt.now(tz.utc), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


def generate_id():
    return str(uuid())[:PASTE_ID_LENGTH]


@app.route('/')
def index():
    session_id = request.cookies.get(COOKIE_NAME)
    if session_id:
        session = Session.query.filter_by(id=session_id).first()
        if session:
            user = User.query.filter_by(id=session.user_id).first()
            return render_template('index.html', username=user.username, authenticated=True)
    return render_template('index.html', username='Unknown', authenticated=False)


@app.route('/paste', methods=['GET'])
def redirect_to_root():
    return redirect('./', 301) # redirect(url_for('index'))


@app.route('/paste/<paste_id>')
def view_paste(paste_id):
    return render_template('paste.html', paste_id=paste_id)


@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)


@app.route('/api/register', methods=['POST'])
def register():
    if request.method != 'POST':
        return jsonify({'error': 'invalid request method'}), 405
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return jsonify({'error': 'username and password are required'}), 400
    username = username.strip()[:32]
    password = password.strip()
    if User.by_username(username):
        return jsonify({'error': 'username already exists'}), 400
    salt = uuid().hex[:32]
    password_hash = f'{password}{salt}'
    password_hash = hashlib.sha256(password_hash.encode('utf-8')).hexdigest()
    user = User(username=username, password_hash=password_hash, password_salt=salt)
    db.session.add(user)
    db.session.commit()
    response = jsonify({'username': username})
    return response, 200


@app.route('/api/login', methods=['POST'])
def login():
    if request.method != 'POST':
        return jsonify({'error': 'invalid request method'}), 405
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return jsonify({'error': 'username and password are required'}), 400
    username = username.strip()[:32]
    password = password.strip()
    user = User.by_username(username)
    if not user:
        return jsonify({'error': 'username does not exists'}), 400
    if user.password_hash != hashlib.sha256(f'{password}{user.password_salt}'.encode('utf-8')).hexdigest()[:64]:
        return jsonify({'error': 'incorrect password'}), 400
    session_id = uuid().hex[:32]
    session = Session(id=session_id, user_id=user.id)
    db.session.add(session)
    db.session.commit()
    response = jsonify({'username': username})
    response.set_cookie(COOKIE_NAME, session_id, max_age=30*86400, httponly=True, secure=False, samesite='Strict')  #TODO secure=True
    return response, 200


@app.route('/api/logout', methods=['POST'])
def logout():
    if request.method != 'POST':
        return jsonify({'error': 'invalid request method'}), 405
    session_id = request.cookies.get(COOKIE_NAME)
    if session_id:
        session = Session.query.filter_by(id=session_id).first()
        if session:
            db.session.delete(session)
            db.session.commit()
    response = jsonify({'success': True})
    response.set_cookie(COOKIE_NAME, '', expires=0)
    return response, 200


@app.route('/api/paste', methods=['POST'])
def create_paste():
    session_id = request.cookies.get(COOKIE_NAME)
    user = None
    if session_id:
        session = Session.query.filter_by(id=session_id).first()
        if session:
            user = User.query.filter_by(id=session.user_id).first()
    if not user:
        return jsonify({'error': 'unauthorized'}), 401
    data = request.get_json()
    if not data:
        return jsonify({'error': 'content is required'}), 400
    content = data.get('text', None)
    image = data.get('image', None)
    if isinstance(content, str):
        content = content.strip()
        if len(content) > TEXT_LENGTH_LIMIT:
            return jsonify({'error': f'Content exceeds {TEXT_LENGTH_LIMIT} character limit'}), 400
        if not content:
            return jsonify({'error': 'text cannot be empty'}), 400
    elif not image:
        return jsonify({'error': 'text or image is required'}), 400
    paste_id = generate_id()
    while Paste.query.filter_by(id=paste_id).first():
        paste_id = generate_id()
    if image:
        paste = Paste(id=paste_id, image=image, size=len(image), user_id=user.id)
        db.session.add(paste)
        db.session.commit()
        return jsonify({
            'id': paste.id,
            'url': f"paste/{paste_id}"
        }), 201
    else:
        paste = Paste(id=paste_id, text=content, size=len(content), user_id=user.id)
        db.session.add(paste)
        db.session.commit()
        return jsonify({
            'id': paste.id,
            'text': content,
            'url': f"paste/{paste_id}"
        }), 201


@app.route('/api/paste/<paste_id>', methods=['GET'])
def get_paste(paste_id):
    paste = Paste.query.filter_by(id=paste_id).first()
    if not paste:
        return jsonify({'error': 'Paste not found'}), 404
    response_data = {
        'id': paste.id,
        'size': paste.size,
        'created_at': paste.created_at
    }
    if paste.image:
        response_data['image'] = paste.image
    else:
        response_data['text'] = paste.text
    return jsonify(response_data), 200


if __name__ == '__main__':
    if not os.path.exists(DATABASE_PATH):
        with app.app_context():  # equivalent to app.app_context().push()
            db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)

