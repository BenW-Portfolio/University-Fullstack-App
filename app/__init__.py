from flask import Flask, render_template
<<<<<<< HEAD
from db.queries.setup import init_db
=======
from queries.setup import init_db
>>>>>>> 660710147f58bb52232d23c8b1b0a8948b8519cd

#* if you need to use a db use it in this format
#* user_db = UserDB("./db/app.db")
#* abstract it

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'supersecret'  # 🔐 Must be set


    with app.app_context():
        init_db()

    @app.route('/')
    def home():
        return render_template('home.html')


    from .auth import auth_bp
    from .applicant import applicant_bp
    from .gs import gs_bp
    from .reviewer import reviewer_bp
    from .cac import cac_bp
    from .recommender import recommender_bp
    from .admin import admin_bp
    

    app.register_blueprint(auth_bp)
    app.register_blueprint(applicant_bp)
    app.register_blueprint(gs_bp)
    app.register_blueprint(reviewer_bp)
    app.register_blueprint(cac_bp)
    app.register_blueprint(recommender_bp)
    app.register_blueprint(admin_bp)

    return app
