from flask import Flask
from flask import request, jsonify, Blueprint
from . import db
import uuid
from config import Config
from .models import User, Organization
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from flask_jwt_extended import get_jwt_identity


bp = Blueprint('api', __name__)


def validate_user_data(data):
    errors = []
    if not data.get('firstName'):
        errors.append({"field": "firstName", "message":
                      "First name is required"})
    if not data.get('lastName'):
        errors.append({"field": "lastName", "message":
                      "Last name is required"})
    if not data.get('email'):
        errors.append({"field": "email", "message": "Email is required"})
    if not data.get('password'):
        errors.append({"field": "password", "message": "Password is required"})
    return errors


@bp.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    errors = validate_user_data(data)
    if errors:
        return jsonify({"errors": errors}), 422

    user = User(
        userId=str(uuid.uuid4()),
        firstName=data['firstName'],
        lastName=data['lastName'],
        email=data['email'],
        phone=data.get('phone')
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()

    organization = Organization(
        orgId=str(uuid.uuid4()),
        name=f"{user.firstName}'s Organization",
        users=[user]
    )
    db.session.add(organization)
    db.session.commit()

    access_token = create_access_token(identity=user.userId)
    return jsonify({
        "status": "success",
        "message": "Registration successful",
        "data": {
            "accessToken": access_token,
            "user": {
                "userId": user.userId,
                "firstName": user.firstName,
                "lastName": user.lastName,
                "email": user.email,
                "phone": user.phone
            }
        }
    }), 201


@bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user and user.check_password(data['password']):
        access_token = create_access_token(identity=user.userId)
        return jsonify({
            "status": "success",
            "message": "Login successful",
            "data": {
                "accessToken": access_token,
                "user": {
                    "userId": user.userId,
                    "firstName": user.firstName,
                    "lastName": user.lastName,
                    "email": user.email,
                    "phone": user.phone
                }
            }
        }), 200
    return jsonify({"status": "Bad request", "message":
                   "Authentication failed"}), 401


@bp.route('/api/users/<id>', methods=['GET'])
@jwt_required()
def get_user(id):
    current_user_id = get_jwt_identity()
    user = User.query.filter_by(userId=current_user_id).first()
    if not user:
        return jsonify({"status": "Bad request", "message":
                       "User not found"}), 404
    return jsonify({
        "status": "success",
        "message": "User retrieved",
        "data": {
            "userId": user.userId,
            "firstName": user.firstName,
            "lastName": user.lastName,
            "email": user.email,
            "phone": user.phone
        }
    }), 200


@bp.route('/api/organisations', methods=['GET'])
@jwt_required()
def get_organisations():
    current_user_id = get_jwt_identity()
    user = User.query.filter_by(userId=current_user_id).first()
    if not user:
        return jsonify({"status": "Bad request", "message":
                       "User not found"}), 404
    organisations = [{"orgId": org.orgId, "name": org.name, "description":
                     org.description} for org in user.organizations]
    return jsonify({
        "status": "success",
        "message": "Organisations retrieved",
        "data": {"organisations": organisations}
    }), 200


@bp.route('/api/organisations/<orgId>', methods=['GET'])
@jwt_required()
def get_organization(orgId):
    current_user_id = get_jwt_identity()
    org = Organization.query.filter_by(orgId=orgId).first()
    if not org or current_user_id not in [user.userId for user in org.users]:
        return jsonify({"status": "Bad request", "message":
                       "Organization not found or access denied"}), 404
    return jsonify({
        "status": "success",
        "message": "Organization retrieved",
        "data": {
            "orgId": org.orgId,
            "name": org.name,
            "description": org.description
        }
    }), 200


@bp.route('/api/organisations', methods=['POST'])
@jwt_required()
def create_organization():
    data = request.get_json()
    if not data.get('name'):
        return jsonify({"status": "Bad request", "message":
                       "Name is required"}), 400
    current_user_id = get_jwt_identity()
    user = User.query.filter_by(userId=current_user_id).first()
    if not user:
        return jsonify({"status": "Bad request", "message":
                       "User not found"}), 404

    org = Organization(
        orgId=str(uuid.uuid4()),
        name=data['name'],
        description=data.get('description'),
        users=[user]
    )
    db.session.add(org)
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Organization created successfully",
        "data": {
            "orgId": org.orgId,
            "name": org.name,
            "description": org.description
        }
    }), 201


@bp.route('/api/organisations/<orgId>/users', methods=['POST'])
@jwt_required()
def add_user_to_organization(orgId):
    data = request.get_json()
    user_id = data.get('userId')
    if not user_id:
        return jsonify({"status": "Bad request", "message":
                       "User ID is required"}), 400

    org = Organization.query.filter_by(orgId=orgId).first()
    user = User.query.filter_by(userId=user_id).first()
    if not org or not user:
        return jsonify({"status": "Bad request", "message":
                       "Organization or user not found"}), 404

    org.users.append(user)
    db.session.commit()

    return jsonify({"status": "success", "message":
                   "User added to organization successfully"}), 200


# Register the blueprint
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt = JWTManager(app)

    with app.app_context():
        from . import routes
        app.register_blueprint(routes.bp)
        db.create_all()

    return app
