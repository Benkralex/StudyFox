from config import app

if __name__ == '__main__':
    app.app_context().push()
    app.run(debug=True)