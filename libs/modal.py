import os
import re

import jwt
# from PIL import Image
from flask import jsonify, json, request
from urllib3.packages.six import wraps
from werkzeug.utils import secure_filename
from config import SecretKey, AVATAR_URL
from libs.fcm import fcm
from libs.database import Database as db


class Modal:

    def __init__(self):
        self.app_key = "b7ec-2816ad0b8b27"

    @staticmethod
    def auth_header(rq, data):
        try:
            headers = rq.headers
            sent_token = headers['Authorization']
            jwt_token = sent_token.replace("Bearer", "").strip()
            decoded = jwt.decode(jwt_token, SecretKey, algorithms="HS256")

            decoded_username = decoded['username']
            sent_username = data["username"]

            if decoded_username == sent_username:
                print(decoded)
                return True
            else:
                return False
                # return False
        except Exception as e:
            return False

    @staticmethod
    def get_username(user_id):
        values = {"username": user_id}
        data = db.select("sia_user", "*", **values)
        return data

    @staticmethod
    def get_fees(op_type):
        values = {"operation": op_type}
        rs = db.select("sia_fees", "*", **values)
        if len(rs) > 0:
            return rs[0]['fee_amount']
        else:
            return 0

    @staticmethod
    def decrypt_seed(seed_key, password, secrete_key):
        return seed_key

    @staticmethod
    def get_user_by_user_id(user_id):
        values = {"user_id": user_id}
        data = db.select("sia_user", "*", **values)
        return data

    @staticmethod
    def get_user_by_username(username, email):
        values = {"username": username, "email": email}
        data = db.select("sia_user", "*", **values)
        return data

    @staticmethod
    def get_user_by_code(username, auth_code):
        values = {"username": username, "auth_code": str(auth_code)}
        data = db.select("sia_user", "*", **values)
        return data

    @staticmethod
    def make_response(status, message, data=None):
        rsp = {'status': status, 'message': message, "data": data}
        if status == 100:
            code = 200
        elif status == 404:
            code = 404
        else:
            code = 403
        return jsonify(rsp), code

    @staticmethod
    def send_notification(user_id, fcm_token, bet_status):
        try:
            if fcm_token == "":
                username_info = modal.get_user_by_user_id(user_id)
                if len(username_info) == 0:
                    return False
                fcm_token = username_info[0]['fcm_token']

            message_info = get_notification(bet_status)
            if len(message_info) > 0:
                message = message_info[0]["message"]
                title = message_info[0]["title"]
                message_type = message_info[0]["type"]
                message_dic = {"title": title, "message": message, "type": message_type}
                fcm.send(fcm_token, message_dic)
            return True
        except Exception as e:
            return False

    @staticmethod
    def get_user_info(user_info):
        info = {
            "username": user_info['username'],
            "user_id": user_info['user_id'],
            "fcm_key": user_info['fcm_token'],
            "avatar": AVATAR_URL + user_info['avatar']
        }
        return info


def get_notification(position):
    return db.select_query("select * from  sia_notifications  where position = '" + position + "' ")


def make_this_response(status, message):
    rsp = {'status': status, 'response': message}
    if status == 100:
        code = 200
    elif status == 404:
        code = 404
    else:
        code = 403
    return jsonify(rsp), code


def is_json(myjson):
    try:
        json_object = json.loads(myjson)
    except Exception as e:
        return False
    return True


def is_valid(request):
    if request is None:
        return False
    return True


def return_data(status, message):
    return {'status': status, 'response': message}


def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        print(kwargs)
        print(args)
        token = None
        if 'Authorization' in request.headers:
            sent_token = request.headers['Authorization']
            token = sent_token.replace("Bearer", "").strip()
        if not token:
            return jsonify({'message': 'a valid token is missing'})

        try:
            decoded = jwt.decode(token, SecretKey, algorithms="HS256")
            decoded_username = "ema"  # decoded['username']
            current_user = Modal.get_username(decoded_username)
        except:
            return jsonify({'message': 'token is invalid'})
        return f(current_user, *args, **kwargs)

    return decorator


modal = Modal()
if __name__ == '__main__':
    modal.upload_single_file()
