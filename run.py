from flask import Flask
from controllers.bets import bp_app as bet_mod
from controllers.user import bp_app as user_mod

app = Flask(__name__)

app.register_blueprint(user_mod)
app.register_blueprint(bet_mod, url_prefix="/bet")
app.run(port=8000, host="0.0.0.0", debug=True)
