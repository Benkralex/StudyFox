from config import app
import routes

if __name__ == '__main__':
    app.app_context().push()
    app.run(debug=True)