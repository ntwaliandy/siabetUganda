from flask import Flask, redirect, request, url_for, render_template

from config import MOCK_TEST, DEBUG
from libs.database import DB as DB_CON

application = Flask(__name__)
# application.config.from_object('config')
application.secret_key = "123456789"

if MOCK_TEST:
    DB = DB_CON
else:
    DB = DB_CON


    @application.before_request
    def _connect_db():
        if not MOCK_TEST:
            DB.connect()


    @application.teardown_request
    def _close_db():
        print("looks hmm")
        if not MOCK_TEST and not DB.is_closed():
            DB.close()
