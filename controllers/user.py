from flask import Blueprint, request, jsonify, json
from models.user import User
from libs.modal import Modal as md, modal, token_required

bp_app = Blueprint('mod_user', __name__)


def __init__(self):
    return md.make_response(403, "Not allowed here")


@bp_app.route("/")
def index():
    return md.make_response(403, "Not allowed here")


@bp_app.route("/user/register", methods=["POST"])
def register():
    return User.register_user(request)


@bp_app.route("/user/make_validator", methods=["POST"])
@token_required
def make_validator(current_user):
    return User.make_validator(request)


@bp_app.route("/user/update_profile", methods=["POST"])
def update_profile():
    return User.update_profile(request)


@bp_app.route("/user/search_users", methods=["GET"])
def search_users():
    q = request.args.get("q")
    return User.search_users(q)


@bp_app.route("/user/profile/<user_id>", methods=["GET"])
def profile(user_id):
    return User.get_profile(user_id)


@bp_app.route("/user/follow_user", methods=["POST"])
def follow_user():
    return User.follow_user(request)


@bp_app.route("/user/following/<user_id>", methods=["GET"])
def following(user_id):
    return User.get_following(user_id)


@bp_app.route("/user/followers/<user_id>", methods=["GET"])
def followers(user_id):
    return User.get_followers(user_id)


@bp_app.route("/user/make_transfer", methods=["POST"])
@token_required
def make_payment(current_user):
    return User.make_transfer(request)


@bp_app.route("/user/login", methods=["POST"])
def login():
    return User.login(request)
