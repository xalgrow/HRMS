import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime

app = Flask(__name__)

# Ensure the database path is persistent
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'hrms.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///yourdatabase.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'
db = SQLAlchemy(app)
jwt = JWTManager(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    users = db.relationship('User', backref='role', lazy=True)

    def __repr__(self):
        return f'<Role {self.name}>'

class Payroll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    salary = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f'<Payroll {self.user_id} - {self.salary}>'

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return f'<Attendance {self.user_id} - {self.date} - {self.status}>'

@app.route('/')
def home():
    return "Server is running!"

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"message": "User with this email already exists."}), 400
    new_user = User(
        username=data['username'],
        email=data['email'],
        password=data['password'],
        role_id=data['role_id']
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered successfully!"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user and user.password == data['password']:
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token), 200
    return jsonify({"msg": "Bad username or password"}), 401

@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

@app.route('/admin', methods=['GET'])
@jwt_required()
def admin():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if current_user.role.name != 'Admin':
        return jsonify({"msg": "Admins only!"}), 403
    return jsonify({"msg": "Welcome, Admin!"}), 200

@app.route('/employee/<int:id>', methods=['PUT'])
@jwt_required()
def update_employee(id):
    data = request.get_json()
    employee = User.query.get(id)
    if not employee:
        return jsonify({"msg": "Employee not found"}), 404
    employee.username = data['username']
    employee.email = data['email']
    db.session.commit()
    return jsonify({"msg": "Employee updated successfully"}), 200

@app.route('/employee/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_employee(id):
    employee = User.query.get(id)
    if not employee:
        return jsonify({"msg": "Employee not found"}), 404
    db.session.delete(employee)
    db.session.commit()
    return jsonify({"msg": "Employee deleted successfully"}), 200

@app.route('/role', methods=['POST'])
@jwt_required()
def create_role():
    data = request.get_json()
    if Role.query.filter_by(name=data['name']).first():
        return jsonify({"msg": "Role already exists"}), 400
    new_role = Role(name=data['name'])
    db.session.add(new_role)
    db.session.commit()
    return jsonify({"msg": "Role created successfully"}), 201

@app.route('/role/<int:id>', methods=['PUT'])
@jwt_required()
def update_role(id):
    data = request.get_json()
    role = Role.query.get(id)
    if not role:
        return jsonify({"msg": "Role not found"}), 404
    role.name = data['name']
    db.session.commit()
    return jsonify({"msg": "Role updated successfully"}), 200

@app.route('/role/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_role(id):
    role = Role.query.get(id)
    if not role:
        return jsonify({"msg": "Role not found"}), 404
    db.session.delete(role)
    db.session.commit()
    return jsonify({"msg": "Role deleted successfully"}), 200

@app.route('/role', methods=['GET'])
@jwt_required()
def get_roles():
    roles = Role.query.all()
    result = [{"id": role.id, "name": role.name} for role in roles]
    return jsonify(result), 200

@app.route('/payroll', methods=['POST'])
@jwt_required()
def create_payroll():
    data = request.get_json()
    new_payroll = Payroll(user_id=data['user_id'], salary=data['salary'], date=datetime.strptime(data['date'], '%Y-%m-%d'))
    db.session.add(new_payroll)
    db.session.commit()
    return jsonify({"msg": "Payroll created successfully"}), 201

@app.route('/payroll/<int:id>', methods=['PUT'])
@jwt_required()
def update_payroll(id):
    data = request.get_json()
    payroll = Payroll.query.get(id)
    if not payroll:
        return jsonify({"msg": "Payroll record not found"}), 404
    payroll.salary = data['salary']
    payroll.date = datetime.strptime(data['date'], '%Y-%m-%d')
    db.session.commit()
    return jsonify({"msg": "Payroll updated successfully"}), 200

@app.route('/payroll/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_payroll(id):
    payroll = Payroll.query.get(id)
    if not payroll:
        return jsonify({"msg": "Payroll record not found"}), 404
    db.session.delete(payroll)
    db.session.commit()
    return jsonify({"msg": "Payroll deleted successfully"}), 200

@app.route('/attendance', methods=['POST'])
@jwt_required()
def mark_attendance():
    data = request.get_json()
    new_attendance = Attendance(user_id=data['user_id'], date=datetime.strptime(data['date'], '%Y-%m-%d'), status=data['status'])
    db.session.add(new_attendance)
    db.session.commit()
    return jsonify({"msg": "Attendance marked successfully"}), 201

@app.route('/attendance', methods=['GET'])
@jwt_required()
def view_attendance():
    user_id = request.args.get('user_id')
    attendance_records = Attendance.query.filter_by(user_id=user_id).all()
    result = [{"date": record.date.strftime('%Y-%m-%d'), "status": record.status} for record in attendance_records]
    return jsonify(result), 200

@app.route('/attendance/report', methods=['GET'])
@jwt_required()
def attendance_report():
    start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d')
    end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d')
    attendance_records = Attendance.query.filter(Attendance.date >= start_date, Attendance.date <= end_date).all()
    result = {}
    for record in attendance_records:
        if record.user_id not in result:
            result[record.user_id] = {'Present': 0, 'Absent': 0}
        result[record.user_id][record.status] += 1
    return jsonify(result), 200

@app.route('/payroll/report', methods=['GET'])
@jwt_required()
def payroll_report():
    start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d')
    end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d')
    payroll_records = Payroll.query.filter(Payroll.date >= start_date, Payroll.date <= end_date).all()
    result = {}
    for record in payroll_records:
        if record.user_id not in result:
            result[record.user_id] = 0
        result[record.user_id] += record.salary
    return jsonify(result), 200

@app.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    users = User.query.all()
    result = [{"id": user.id, "username": user.username, "email": user.email, "role_id": user.role_id} for user in users]
    return jsonify(result), 200

if __name__ == '__main__':
    app.config['DEBUG'] = True  # Enable debug mode
    app.run()

