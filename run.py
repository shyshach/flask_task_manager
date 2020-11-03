from app import app
from datetime import timedelta

if __name__ == '__main__':
    app.permanent_session_lifetime = timedelta(minutes=30)

    app.config.update({
        'TESTING': True
    })
    app.run(debug=True, host='0.0.0.0')
