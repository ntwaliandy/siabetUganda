from flask import Blueprint, request, jsonify, json
from models.bets import Bet as Bt
from libs.modal import Modal as md, modal, token_required

bp_app = Blueprint('bet', __name__)


def __init__(self):
    return md.make_response(403, "Not allowed here")


@bp_app.route("/")
def index():
    return md.make_response(403, "Not allowed here")


@bp_app.route("/create_topic", methods=["POST"])
@token_required
def create_topic(current_user):
    return Bt.create_topic(request)


@bp_app.route("/place_bet", methods=["POST"])
@token_required
def place_bet(current_user):
    return Bt.place_bet(request)


@bp_app.route("/create_category", methods=["POST"])
@token_required
def create_category(current_user):
    return Bt.create_category(request)


@bp_app.route("/get_user_topics/<user_id>", methods=["GET"])
@token_required
def get_user_topics(current_user, user_id):
    return Bt.get_topics_for_user(user_id)


@bp_app.route("/topics_feed/<user_id>", methods=["GET"])
def topics_feed(user_id):
    q = request.args.get("q")
    return Bt.topics_feed(q, user_id)


@bp_app.route("/pending_topics/<user_id>", methods=["GET"])
@token_required
def pending_topics(current_user, user_id):
    return Bt.get_pending_topics(user_id)


@bp_app.route("/user_bets/<user_id>", methods=["GET"])
def user_bets(user_id):
    return Bt.user_bets(user_id)


@bp_app.route("/leaderboard", methods=["GET"])
def leaderboard():
    return Bt.leaderboard()


@bp_app.route("/execute_bets", methods=["POST"])
def insert_game_result():
    return Bt.insert_game_result(request)


@bp_app.route("/get_categories", methods=["GET"])
def get_categories():
    q = request.args.get("q")
    return Bt.get_all_categories(q)


@bp_app.route("/get_requests/<user_id>", methods=["GET"])
def get_requests(user_id):
    return Bt.get_requests(user_id)


@bp_app.route("/approve_topic", methods=["POST"])
def approve_topic():
    return Bt.approve_topic(request)


@bp_app.route("/make_payouts", methods=["POST"])
def make_payouts():
    return Bt.make_payments_payouts()
