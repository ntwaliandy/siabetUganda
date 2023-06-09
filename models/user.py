import hashlib
import json
import re
import uuid
import random
import jwt
from flask import jsonify

from libs.Stellar import Stellar
from libs.database import Database as Db
from libs.fcm import fcm
from libs.modal import Modal as Md
from config import SecretKey, AVATAR_URL
from stellar_sdk import Server, Keypair, TransactionBuilder, Network


class User:
    def __init__(self):
        self.key = "testKey"

    @staticmethod
    def register_user(rq):
        data = rq.json
        try:
            print(data)
            username = str(data["username"])
            password = data["password"]
            email = data["email"] 

            if username == "" or len(username) < 3 or password == "" or len(password) < 6:
                return Md.make_response(203, "username should be over 3 characters and password over 6")

            if not is_valid_email:
                return Md.make_response(404, "enter a valid email")

            password = hashlib.sha256(password.encode('utf-8')).hexdigest()

            # check_username = Md.get_user_by_username(username, email)
            check_username = Db.select_query("select * from sia_user where username = '" + username + "' or email = '" + email + "'")
            if len(check_username) > 0:
                return Md.make_response(203, "record already exists")
            user_keypair = Keypair.random()
            public_key = user_keypair.public_key
            print(public_key)
            jwt_token = jwt.encode(data, SecretKey, algorithm="HS256")
            seed_key = user_keypair.secret
            print(seed_key)
            mnemonic_phrase = user_keypair.generate_mnemonic_phrase()
            print(mnemonic_phrase)
            # res = Stellar().sponsor_account(public_key, user_keypair)
            user_id = str(uuid.uuid1())
            avatar = random.randint(0, 101)
            is_validator = False
            avatar = "user" + str(avatar) + ".png"
            register_dict = {"user_id": user_id, "avatar": avatar, "username": username, "password": password,
                             "email": email,
                             "public_key": public_key, "jwt_token": jwt_token, "seed_key": seed_key}
            last_id = Db.insert('sia_user', **register_dict)
            avatar_url = AVATAR_URL + avatar
            user_data = {"jwt": jwt_token, "avatar": avatar_url, "user_id": user_id, "username": username,
                         "public_key": public_key, "isValidator": is_validator, "mnemonic_phrase": mnemonic_phrase}
            return Md.make_response(100, "success", user_data)
        except Exception as e:
            return Md.make_response(203, str(e))

    @staticmethod
    def login(rq):
        try:
            data = rq.json
            username = data['username']
            password = data['password']
            password = hashlib.sha256(password.encode('utf-8')).hexdigest()

            auth = auth_user(username, password)
            if len(auth) > 0:
                public_key = auth[0]['public_key']
                seed_key = auth[0]['seed_key']
                user_id = auth[0]['user_id']
                avatar = auth[0]['avatar']
                is_validator = auth[0]['isValidator']
                mnemonic_phrase = Keypair.from_secret(seed_key).generate_mnemonic_phrase()
                avatar_url = AVATAR_URL + avatar

                jwt_token = jwt.encode(data, SecretKey, algorithm="HS256")
                user_data = {"jwt": jwt_token, "avatar": avatar_url, "user_id": user_id, "username": username,
                             "public_key": public_key, "isValidator": is_validator, "mnemonic_phrase": mnemonic_phrase}
                return Md.make_response(100, "success", user_data)
            else:
                return Md.make_response(203, "Invalid username or password")
        except Exception as e:
            return Md.make_response(203, str(e))

    @staticmethod
    def search_users(q):
        res = Db.select_query("select * from sia_user where username Like '" + str(q) + "%' LIMIT 20")
        list_info = []
        for x in res:
            user = Md.get_user_info(x)
            list_info.append(user)
        return jsonify(list_info)

    @staticmethod
    def get_following(user_id):
        res = get_following(user_id)
        user_info = []
        for x in res:
            user = Md.get_user_info(x)
            user_info.append(user)
        return jsonify(user_info)

    @staticmethod
    def get_followers(user_id):
        res = followers(user_id)
        user_info = []
        for x in res:
            user = Md.get_user_info(x)
            user_info.append(user)
        return jsonify(user_info)

    @staticmethod
    def get_profile(user_id):
        follower = len(followers(user_id))
        following = len(get_following(user_id))
        played = len(get_played(user_id))
        won = len(get_won(user_id))
        lost = len(get_lost(user_id))
        info = {"followers": follower,
                "following": following,
                "played": played,
                "won": won,
                "lost": lost}
        return info

    @staticmethod
    def follow_user(data):
        try:
            sender_user_id = data['user_id']
            follow_user_id = data['follow_user_id']
            follow_status = data['follow_status']
            follow_key = follow_user_id + sender_user_id

            if sender_user_id == follow_user_id:
                return Md.make_response(101, "follow self not allowed")

            get_user = Md.get_user_by_user_id(sender_user_id)
            if len(get_user) == 0:
                return Md.make_response(404, "sender user id not found")

            get_follow_user = Md.get_user_by_user_id(follow_user_id)
            if len(get_follow_user) == 0:
                return Md.make_response(404, "following user id not found")

            try:
                register_dict = {"follow_key": follow_key, "user_id": sender_user_id,
                                 "following_user_id": follow_user_id,
                                 "follow_status": follow_status}
                last_id = Db.insert('sia_user_follow', **register_dict)
                return Md.make_response(100, "success")
            except Exception as e:
                register_dict = {"follow_status": follow_status}
                Db.Update("sia_user_follow", "follow_key = '" + follow_key + "'", **register_dict)
                return Md.make_response(100, "updated")

        except Exception as e:

            return Md.make_response(203, "failed")

    @staticmethod
    def update_profile(rq):
        try:
            data = rq.json
            user_id = data['user_id']
            fcm = data['fcm']
            user_info = Md.get_user_by_user_id(user_id)
            if len(user_info) == 0:
                return Md.make_response(404, "sender user id not found")

            # fcm = data['fcm']
            is_validator = user_info[0]['isValidator']

            register_dict = {"fcm_token": fcm}
            Db.Update("sia_user", "user_id = '" + user_id + "'", **register_dict)
            jwt_token = jwt.encode(data, SecretKey, algorithm="HS256")
            user_data = {"jwt": jwt_token, "isValidator": is_validator}
            return Md.make_response(100, "success", user_data)
        except Exception as e:
            return Md.make_response(203, "failed")

    @staticmethod
    def change_password_init(rq):
        try:
            data = rq.json
            username = data['username']
            email = data['email']
            user_info = Md.get_user_by_username(username, email)
            if len(user_info) == 0:
                return Md.make_response(404, "username or email not found")

            code = 55555
            register_dict = {"auth_code": code}
            Db.Update("sia_user", "username = '" + username + "'", **register_dict)
            return Md.make_response(100, "code sent")
        except Exception as e:
            return Md.make_response(203, "failed")

    @staticmethod
    def change_password(rq):
        try:
            data = rq.json
            username = data['username']
            code = data['code']
            password = data['password']
            confirm_password = data['confirm_password']

            if password != confirm_password:
                return Md.make_response(404, "passwords don't match")

            if len(password) < 6:
                return Md.make_response(404, "passwords too short. password should be more than 6 characters")

            user_info = Md.get_user_by_code(username, code)
            if len(user_info) == 0:
                return Md.make_response(404, "code not found for user")
            password = hashlib.sha256(password.encode('utf-8')).hexdigest()

            register_dict = {"password": password}
            Db.Update("sia_user", "username = '" + username + "'", **register_dict)
            return Md.make_response(100, "Your password has been reset")
        except Exception as e:
            return Md.make_response(203, "failed")

    @staticmethod
    def update_favorite(rq):
        try:
            data = rq.json
            user_id = data['user_id']
            cat_id = data['category_name']
            user_info = Md.get_user_by_user_id(user_id)
            if len(user_info) == 0:
                return Md.make_response(404, "sender user id not found")

            favorites = user_info[0]['favorites']
            fav_list = []
            if favorites == "":
                fav_list.append(cat_id)
            else:
                fav_list = json.loads(favorites)
                if cat_id not in fav_list:
                    fav_list.append(cat_id)
                else:
                    fav_list.remove(cat_id)
            register_dict = {"favorites": json.dumps(fav_list)}
            Db.Update("sia_user", "user_id = '" + user_id + "'", **register_dict)
            return Md.make_response(100, "success")
        except Exception as e:
            print(str(e))
            return Md.make_response(203, "failed")

    @staticmethod
    def make_validator(rq):
        try:
            data = rq.json
            user_id = data['user_id']
            is_validator = data['isValidator']
            username_info = Md.get_user_by_user_id(user_id)
            if len(username_info) == 0:
                return Md.make_response(404, "user not found")
            fcm_key = username_info[0]['fcm_token']
            list_keys = [fcm_key]

            if is_validator:
                fcm.manage_subscription(list_keys, "validators", "subscribe")
            else:
                fcm.manage_subscription(list_keys, "validators", "unsubscribe")

            register_dict = {"isValidator": is_validator}
            Db.Update("sia_user", "user_id = '" + user_id + "'", **register_dict)
            return Md.make_response(100, "success")

        except Exception as e:
            return Md.make_response(203, "failed" + str(e))

    @staticmethod
    def make_transfer(rq):
        try:
            data = rq.json
            user_id = data['user_id']
            amount = int(data['amount'])
            sent_signature = data['signature']
            sender_username_info = Md.get_user_by_user_id(user_id)
            if len(sender_username_info) == 0:
                return Md.make_response(404, "user not found")
            sender_secret = sender_username_info[0]['seed_key']
            sender_username = sender_username_info[0]['username']

            if amount > 0:
                receiver = data['receiver']
                asset_code = data['asset_code']
                asset_issuer = data['asset_issuer']
                memo = data['memo']
                signature = user_id + str((amount * 3333)) + receiver + memo + asset_issuer
                amount = data['amount']

                print(signature)
                if signature != sent_signature:
                    return Md.make_response(203, "server error.")

                sender_key_pair = Keypair.from_secret(sender_secret)

                txn_hash = Stellar().make_payment(sender_key_pair, receiver, asset_code, asset_issuer,
                                                  amount, memo)
                response = {"hash": txn_hash}
                receiver_info = get_user_by_key(receiver)
                if len(receiver_info) > 0:
                    receiver_fcm = receiver_info[0]['fcm_token']
                    message = "You have received " + amount + " " + asset_code + " from " + sender_username
                    title = "Received Payment"
                    message_type = "transaction"
                    message_dic = {"title": title, "message": message, "type": message_type}
                    fcm.send(receiver_fcm, message_dic)
                Md.send_notification("", sender_username_info[0]['fcm_token'], "send_money")
                return Md.make_response(100, "success", response)
        except Exception as e:
            return Md.make_response(203, str(e))


def get_played(user_id):
    res = Db.select_query("select * from sia_bets where user_id = '" + user_id + "'")
    return res


def get_user_by_key(public_key):
    res = Db.select_query("select * from sia_user where public_key = '" + public_key + "'")
    return res


def get_won(user_id):
    res = Db.select_query("select * from sia_bets where bet_final_result = 'won' and  user_id = '" + user_id + "'")
    return res


def get_category_by_name(category_name):
    res = Db.select_query("select * from sia_category  where category_name = '" + category_name + "'")
    return res


def get_lost(user_id):
    res = Db.select_query("select * from sia_bets where bet_final_result = 'lost' and  user_id = '" + user_id + "'")
    return res


def followers(user_id):
    res = Db.select_query("select * from sia_user_follow f inner join  sia_user u ON f.user_id = u.user_id where "
                          "following_user_id = '" + user_id + "'")
    return res


def get_following(user_id):
    res = Db.select_query(
        "select * from sia_user_follow f inner join sia_user u ON f.following_user_id = u.user_id where f.user_id = '" + user_id + "'")
    return res


def is_valid_email(email):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if re.match(regex, email):
        return True
    else:
        return False


def auth_user(username, password):
    values = {"username": username, "password": password}
    data = Db.select("sia_user", "*", **values)
    return data
