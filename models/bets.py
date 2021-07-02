import uuid

import jwt
from flask import jsonify, request

from libs.Stellar import Stellar
from libs.database import Database as Db
from libs.modal import Modal as Md
from config import SecretKey, AVATAR_URL
from stellar_sdk import Server, Keypair, TransactionBuilder, Network
from datetime import datetime, timedelta


class Bet:
    def __init__(self):
        self.key = "testKey"
        if not Md.auth_header(request, "testKey"):
            return Md.make_response(203, "Authentication failed")

    @staticmethod
    def approve_topic(rq):
        try:
            data = rq.json
            topic_id = data['topic_id']
            approval_status = data['approval_status']
            approved_by = data['approved_by']

            sender_username_info = Md.get_user_by_user_id(approved_by)
            if len(sender_username_info) == 0:
                return Md.make_response(404, "user not found")
            topic = get_pending_topic_detail(topic_id)
            if len(topic) == 0:
                return Md.make_response(404, "not found")

            user_info = Md.get_user_by_user_id(topic[0]['topic_user_id'])

            if approval_status == "approved":
                fees = Md.get_fees("approve_topic")
                if fees == 0:
                    return Md.make_response(203, "fee not found")
                recipient_public_key = user_info[0]['public_key']
                tp_id = topic[0]['tp_id']
                memo = "approved " + str(tp_id)
                sender_key_pair = Keypair.from_secret(Stellar().airdrop_account)
                asset_code = Stellar().bet_token
                asset_issuer = Stellar().bet_token_issuer

                txn_hash = Stellar().make_payment(sender_key_pair, recipient_public_key, asset_code, asset_issuer,
                                                  fees, memo)

                topic_info = {"approval_status": approval_status, "reward_hash": txn_hash, "approved_by": approved_by}
            else:
                approval_status = "rejected"
                topic_info = {"approval_status": approval_status, "approved_by": approved_by}
            Db.Update("sia_topic", "topic_id = '" + topic_id + "'", **topic_info)
            return Md.make_response(100, approval_status, topic_info)
        except Exception as e:
            return Md.make_response(403, str(e))

    @staticmethod
    def make_payments_payouts():
        return make_payouts()

    @staticmethod
    def insert_game_result(rq):
        try:
            payable = False
            data = rq.json
            # check the time of the game
            # only complete when the game has completed
            topic_id = data['topic_id']
            final_result = data['final_result']
            posted_by = data['posted_by']
            game_status = data['game_status']
            memo = "sia"
            topic = get_topic_detail(topic_id)
            if len(topic) == 0:
                return Md.make_response(404, "not found")

            if game_status == "finished":
                topic_bets = get_all_bets_for_topic(topic_id)

                for x in topic_bets:
                    payable = False
                    bet_id = x['bet_id']
                    bet_answer = x['bet_answer']
                    stake_amount = x['stake_amount']
                    match_status = x['match_status']
                    public_key = x['public_key']
                    bt_id = x['bt_id']
                    user_id = x['user_id']
                    match_id = x['match_id']
                    if match_status == "matched":
                        if bet_answer == final_result:
                            bet_final_result = "won"
                            memo = "win " + str(match_id)
                            payable = True
                        else:
                            payable = False
                            bet_final_result = "lost"
                    else:
                        payable = True
                        memo = "refund" + str(bt_id)
                        bet_final_result = "refundable"
                    print(bet_final_result)
                    if payable:
                        try:
                            payable_bet = {
                                "match_id": match_id,
                                "user_id": user_id,
                                "memo": memo,
                                "amount": stake_amount,
                                "bet_id": bet_id,
                                "reason": bet_final_result,
                                "public_key": public_key
                            }
                            last_id = Db.insert('sia_payable_bets', **payable_bet)
                        except Exception as e:
                            print(str(e))

                    bet_info = {"bet_final_result": bet_final_result, "bet_status": "closed"}
                    topic_info = {"topic_status": game_status}
                    # Db.Update("sia_bet_match ", "bet_match_id = '" + bet_match_id + "'", **matchInfo)
                    Db.Update("sia_topic", "topic_id = '" + topic_id + "'", **topic_info)
                    Db.Update("sia_bets", "bet_id = '" + bet_id + "'", **bet_info)
            make_payouts()
            return Md.make_response(100, "operations complete")
        except Exception as e:
            return Md.make_response(403, str(e))

    @staticmethod
    def place_bet(rq):
        try:

            enc_password = ''
            data = rq.json
            print(data)

            user_id = str(data["user_id"])
            topic_id = data["topic_id"]
            stake_amount = data["stake_amount"]
            asset_code = Stellar().bet_token
            asset_issuer = Stellar().bet_token_issuer
            opponent_user_id = data["opponent_user_id"]
            bet_type = data["bet_type"]
            answer = data["answer"]
            answer_params = ["Yes", "No"]
            bet_status = 'unmatched'
            memo = "demo_sia_bet"
            txn_hash = ""
            opponent_bet_id = data["opponent_bet_id"]
            opponent_info = None
            bet_id = str(uuid.uuid1())

            topic = get_topic_detail(topic_id)
            if len(topic) == 0:
                return Md.make_response(404, "not found")

            if user_id == "" or topic_id == "":
                return Md.make_response(403, "fill all required fields")

            if answer not in answer_params:
                return Md.make_response(403, "Invalid answer")

            sender_username_info = Md.get_user_by_user_id(user_id)
            if len(sender_username_info) == 0:
                return Md.make_response(404, "user not found")

            sender_secret = sender_username_info[0]['seed_key']

            topic_detail = get_topic_detail(topic_id)
            if len(topic_detail) == 0:
                return Md.make_response(404, "topic_id not found")

            if opponent_bet_id != "":
                opponent_info = get_opponent(answer, topic_id, stake_amount, opponent_bet_id)
                if len(opponent_info) == 0:
                    return Md.make_response(404, "opponent not found")
                else:
                    bet_status = 'matched'
            else:
                if bet_type == 'p2p':
                    opponent_info = Md.get_user_by_user_id(opponent_user_id)
                    if len(opponent_info) == 0:
                        return Md.make_response(404, "opponent_username not found")
                    else:
                        bet_status = 'unmatched'
                else:
                    opponent_info = get_worth_opponent(user_id, answer, topic_id, stake_amount)
                    if len(opponent_info) > 0:
                        bet_status = 'matched'

            if len(opponent_info) > 0 and bet_status == 'matched':
                opponent_user_id = opponent_info[0]['user_id']
                opponent_bet_id = opponent_info[0]['bet_id']

            recipient_public_key = Stellar().escrowAccount
            sender_key_pair = Keypair.from_secret(sender_secret)
            print(sender_secret)
            txn_hash = Stellar().make_payment(sender_key_pair, recipient_public_key, asset_code, asset_issuer,
                                              stake_amount, memo)

            bet_dict = {
                "bet_txn_hash": txn_hash,
                "bet_id": bet_id,
                "user_id": user_id,
                "topic_id": topic_id,
                "bet_type": bet_type,
                "opponent_user_id": opponent_user_id,
                "stake_amount": stake_amount,
                "asset_code": asset_code,
                "asset_issuer": asset_issuer,
                "bet_answer": answer,
                "match_status": bet_status
            }
            last_id = Db.insert('sia_bets', **bet_dict)
            if bet_status == 'matched':
                update_bet_matching(topic_id, txn_hash, opponent_bet_id, bet_id, stake_amount, user_id,
                                    opponent_user_id)
            user_data = {"txn_hash": txn_hash, "bet_id": bet_id}
            return Md.make_response(100, "bet placed", user_data)
        except Exception as e:
            return Md.make_response(403, "Not enough funds on your account" + str(e))

    @staticmethod
    def create_topic(rq):
        data = rq.json
        try:
            user_id = str(data["user_id"])
            topic_title = data["topic_title"]
            topic_question = data["topic_question"]
            topic_category_id = data["topic_category_id"]
            if topic_title == "" or topic_question == "" or topic_category_id == "":
                return Md.make_response(403, "Failed")

            check_username = Md.get_user_by_user_id(user_id)
            if len(check_username) == 0:
                return Md.make_response(203, "user not found")
            fees = Md.get_fees("create_topic")
            if fees == 0:
                return Md.make_response(203, "fee not found")
            sender_secret_phrase = check_username[0]['seed_key']
            recipient_public_key = Stellar().escrowAccount
            asset_code = Stellar().bet_token
            asset_issuer = Stellar().bet_token_issuer
            memo = "bet_topic"
            sender_secret_key = Keypair.from_secret(sender_secret_phrase)
            print(sender_secret_key.secret)

            txn_id = Stellar().make_payment(sender_secret_key, recipient_public_key, asset_code, asset_issuer, fees,
                                            memo)
            bet_id = txn_id
            register_dict = {
                "topic_user_id": user_id,
                "topic_id": bet_id,
                "topic_title": topic_title,
                "topic_type_id": 1,
                "topic_question": topic_question,
                "topic_start_date": data["topic_start_date"],
                "topic_category_id": topic_category_id
            }
            last_id = Db.insert('sia_topic', **register_dict)
            user_data = {"topic_id": bet_id}
            return Md.make_response(100, "topic created", user_data)
        except Exception as e:
            return Md.make_response(403, str(e))

    @staticmethod
    def get_topics_for_user(user_id):
        return None

    @staticmethod
    def topics_feed(user_id):
        list_info = []
        categories = get_categories()

        for x in categories:
            x['isFavorite'] = True
            topics = get_topics_for_category(x['category_id'])
            topics_dic = {}
            bet_info = []
            for y in topics:
                topic_start_date = y['topic_start_date']
                topic_end_date = y['topic_end_date']
                datee = topic_start_date.strftime("%Y-%m-%d %H:%M:%S")
                y['start_date'] = datee

                z = {}
                bets = get_bets_for_topic(y['topic_id'])
                y['bets'] = bets
                y['bets_placed'] = len(bets)
                bet_info.append(y)
            if len(bet_info) > 0:
                x['topics'] = bet_info
                list_info.append(x)
        return jsonify(list_info)

    @staticmethod
    def create_category(rq):
        data = rq.json
        try:
            category_name = data['category_name']
            register_dict = {
                "category_name": category_name,
            }
            last_id = Db.insert('sia_category', **register_dict)
            user_data = {"category_id": last_id, "message": "category created"}
            return Md.make_response(100, user_data)
        except Exception as e:
            return Md.make_response(203, str(e))

    @staticmethod
    def get_all_categories(q):
        info = get_categories()

        res_data = []
        if q == "home":
            res_data = [{"label": "All", "value": ""}, {"label": "Favorites", "value": ""},
                        {"label": "My Topics", "value": ""}]

        for x in info:
            data = {"label": x['category_name'], "value": x['category_id']}
            res_data.append(data)
        return jsonify(res_data)

    @staticmethod
    def user_bets(user_id):
        try:
            res = get_all_user_bets(user_id)
            bets = []
            for x in res:
                creator_info = Md.get_user_by_user_id(x['topic_user_id'])
                opponent_info = Md.get_user_by_user_id(x['opponent_user_id'])
                if len(creator_info) > 0 and len(opponent_info) > 0:
                    opponent_username = opponent_info[0]['username']
                    opponent_avatar = AVATAR_URL + opponent_info[0]['avatar']
                    creator_username = creator_info[0]['username']
                    response = {
                        "topic_question": x['topic_question'],
                        "bet_answer": x['bet_answer'],
                        "bet_status": x['bet_status'],
                        "match_status": x['match_status'],
                        "avatar": AVATAR_URL + x['avatar'],
                        "bet_type": x['bet_type'],
                        "bt_id": x['bt_id'],
                        "bet_id": x['bet_id'],
                        "opponent_user_id": x['opponent_user_id'],
                        "stake_amount": x['stake_amount'],
                        "us_id": x['us_id'],
                        "user_id": x['user_id'],
                        "topic_id": x['topic_id'],
                        "bet_final_result": x['bet_final_result'],
                        "opponent_username": opponent_username,
                        "opponent_avatar": opponent_avatar,
                        "creator_username": creator_username
                    }
                    bets.append(response)
            return jsonify(bets)
        except Exception as e:
            return Md.make_response("203", str(e))

    @staticmethod
    def leaderboard():
        rs = get_leader_board()
        return jsonify(rs)


def update_bet_matching(topic_id, txn_id, opponent_bet_id, bet_id, stake_amount, user_id, opponent_user_id):
    register_dict = {
        "bet_match_id": txn_id,
        "topic_id": topic_id,
        "user_one_bet_id": bet_id,
        "user_two_bet_id": opponent_bet_id,
        "user_one_id": user_id,
        "user_two_id": opponent_user_id,
        "stake_amount": stake_amount,
    }

    match_id = Db.insert('sia_bet_match', **register_dict)
    update_user_one_status = {
        "match_status": 'matched',
        "opponent_user_id": opponent_user_id,
        "match_id": match_id
    }
    update_user_two_status = {
        "match_status": 'matched',
        "opponent_user_id": user_id,
        "match_id": match_id

    }

    Db.Update("sia_bets", "bet_id = '" + bet_id + "'", **update_user_one_status)
    Db.Update("sia_bets", "bet_id = '" + opponent_bet_id + "'", **update_user_two_status)


def make_payouts():
    try:
        pending_payouts = get_all_payouts()
        if len(pending_payouts):
            Md.make_response(404, "No pending payouts")

        pay_id = str(uuid.uuid1())
        server = Server(Stellar().horizon)
        sender_account = server.load_account(Stellar().escrowAccount)
        base_fee = server.fetch_base_fee()
        sender_keypair = Keypair.from_secret(Stellar().escrowAccountPvKey)

        transaction_builder = TransactionBuilder(
            source_account=sender_account,
            network_passphrase=Stellar().network_passphrase,
            base_fee=base_fee,
        )
        transaction_builder.add_text_memo("payment")

        for x in pending_payouts:
            memo = x['memo']
            recipient_public_key = x['public_key']
            amount = x['amount']
            p_id = x['p_id']
            asset_code = Stellar().bet_token
            asset_issuer = Stellar().bet_token_issuer

            transaction_builder.append_payment_op(recipient_public_key, amount, asset_code,
                                                  asset_issuer)
            txn_info = {"pay_id": pay_id}
            Db.Update("sia_payable_bets ", "p_id = " + str(p_id) + "", **txn_info)

        transaction = transaction_builder.build()
        transaction.sign(sender_keypair)
        response = server.submit_transaction(transaction)
        try:
            txn_hash = response['hash']
            txn_info = {"txn_hash": txn_hash, "pay_status": "paid"}
            Db.Update("sia_payable_bets ", "pay_id = '" + pay_id + "'", **txn_info)
            return Md.make_response(100, txn_hash)

        except Exception as e:
            txn_info = {"pay_status": "failed", "pay_response": str(response)}
            Db.Update("sia_payable_bets ", "pay_id = '" + pay_id + "'", **txn_info)
            return Md.make_response(203, str(e))

    except Exception as e:
        return Md.make_response(203, str(e))


def get_topic_detail(topic_id):
    values = {"topic_id": topic_id, "topic_status": "active"}
    return Db.select("sia_topic", "*", **values)


def get_pending_topic_detail(topic_id):
    values = {"topic_id": topic_id, "approval_status": "pending", "reward_hash": ""}
    return Db.select("sia_topic", "*", **values)


def get_categories():
    return Db.select_query("select * from  sia_category ")


def get_all_payouts():
    return Db.select_query("select * from sia_payable_bets where txn_hash = '' AND pay_status='pending' LIMIT 100  ")


def get_bets_feed():
    return Db.select_query("select * from sia_topic t  INNER JOIN sia_category c ON t.topic_category_id = "
                           "c.category_id ")


def get_topics_for_category(category_id):
    category_id = str(category_id)
    return Db.select_query("select * from sia_topic t INNER JOIN sia_user u ON t.topic_user_id = u.user_id where "
                           "t.topic_category_id = " + category_id + " AND approval_status = 'approved' and topic_status='active' order by topic_start_date desc")


def get_worth_opponent(user_id, answer, topic_id, amount):
    return Db.select_query(
        "select * from sia_bets  b  INNER JOIN sia_user u ON b.user_id = u.user_id WHERE b.topic_id "
        "= '" + topic_id + "' AND bet_answer!= '" + answer + "' AND bet_type = 'random'  AND match_status = 'unmatched' AND  stake_amount = " + amount + " AND b.user_id !='" + user_id + "'LIMIT 1 ")


def get_opponent(answer, topic_id, amount, bet_id):
    return Db.select_query(
        "select * from sia_bets  b  INNER JOIN sia_user u ON b.user_id = u.user_id WHERE b.topic_id "
        "= '" + topic_id + "' AND bet_answer!= '" + answer + "' AND match_status = 'unmatched' AND  stake_amount = " + amount + " AND b.bet_id ='" + bet_id + "'LIMIT 1 ")


def get_all_bets_for_topic(topic_id):
    return Db.select_query(
        "select * from sia_bets b INNER JOIN sia_user u ON b.user_id = u.user_id  where topic_id =  '" + topic_id + "' AND bet_status = 'open'")


def get_topic_for_user(topic_id, user_id):
    return Db.select_query(
        "select * from  sia_topic t INNER JOIN sia_user u ON t.user_id = u.user_id  where topic_id =  " + topic_id + " AND user_id = '" + user_id + "' AND topic_status='active'")


def get_players(match_id):
    return Db.select_query("select * from sia_bets  where match_id =  " + match_id + " AND bet_status = 'open'")


def get_matched_bets(topic_id):
    return Db.select_query("select * from sia_bet_match   where topic_id =  '" + topic_id + "' AND bet_status = 'open'")


def get_all_user_bets(user_id):
    return Db.select_query("select * from sia_bets  b  INNER JOIN sia_user u ON b.user_id = u.user_id INNER JOIN "
                           "sia_topic t ON b.topic_id = t.topic_id WHERE b.user_id = '" + user_id + "' order by bt_id DESC LIMIT 10")


def get_leader_board():
    return Db.select_query(
        "select *,sum(stake_amount) as stake from sia_bets  b  INNER JOIN sia_user u ON b.user_id = u.user_id  "
        "WHERE bet_final_result = 'won' group by b.user_id order by stake desc")


def get_bets_for_topic(topic_id):
    res = Db.select_query("select * from sia_bets  b  INNER JOIN sia_user u ON b.user_id = u.user_id WHERE b.topic_id "
                          "= '" + topic_id + "' AND match_status='unmatched'")
    bets = []
    for x in res:
        response = {
            "bet_answer": x['bet_answer'],
            "bet_status": x['bet_status'],
            "avatar": AVATAR_URL + x['avatar'],
            "bet_type": x['bet_type'],
            "bt_id": x['bt_id'],
            "bet_id": x['bet_id'],
            "opponent_user_id": x['opponent_user_id'],
            "stake_amount": x['stake_amount'],
            "us_id": x['us_id'],
            "user_id": x['user_id'],
            "topic_id": x['topic_id'],
            "username": x['username']
        }
        bets.append(response)
    return bets
