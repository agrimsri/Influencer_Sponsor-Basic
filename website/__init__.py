from flask import Flask
from flask_login import LoginManager
from .models import db,User
from .api_controller import api

def create_app():
    myapp = Flask(__name__)
    myapp.config['SECRET_KEY'] = 'mysecretkey'
    
    myapp.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'
    db.init_app(myapp)
    api.init_app(myapp)
    
    from .auth import auth
    from .views import views
    
    myapp.register_blueprint(views,url_prefix = '/')
    myapp.register_blueprint(auth,url_prefix = '/auth')
    
    with myapp.app_context():
        db.create_all()
    

    login_manager = LoginManager()
    login_manager.login_view = 'views.home'
    login_manager.init_app(myapp)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    return myapp