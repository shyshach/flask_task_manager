from flask import Flask, render_template, request, url_for, redirect, flash, session
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
import requests
import json
import re
import config

app = Flask(__name__)
app.static_folder = 'static'
app.secret_key = "ogokruto"
api_url = config.API_URL  # API GATEWAY url


def login_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        if 'username' in session:
            return test(*args, **kwargs)
        else:
            flash('You need to login first.')
            return redirect(url_for('login'))

    return wrap


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm")
        email = request.form.get("email")
        url = api_url + "createuser"

        if not 3 < len(username) < 20:
            flash('Username must be between 3 and 20 characters')
            return render_template("registration.html")
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Invalid email')
            return render_template("registration.html")
        if not re.match('\d.*[A-Z]|[A-Z].*\d', password):
            flash('Password must contain 1 capital letter and 1 number')
            return render_template("registration.html")
        if len(password) < 8 or len(password) > 50:
            flash('Password must be between 8 and 50 characters')
            return render_template("registration.html")
        data = {
            "username": username,
            "password": generate_password_hash(password),
            "email": email
        }
        response = requests.post(url, json=data)
        if password == confirm and response.status_code == 200:
            flash("You have successfully registered please continue to login", "success")
            return redirect(url_for("login"))
        elif password != confirm:
            flash(u"Passwords do not match", "danger")
            return render_template("registration.html")
        else:
            flash(u"User with that username exists", "danger")
            return render_template("registration.html")
    return render_template("registration.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("name")
        password = request.form.get("password")
        url = api_url + 'login'
        response = requests.post(url, json={"username": username, "password": generate_password_hash(password)})
        pwhash = response.content.decode("utf-8")
        if response.status_code == 200 and check_password_hash(pwhash, password):
            session["username"] = username

            return render_template("index.html")
        else:
            flash("Bad credentials", "danger")
            return render_template("login.html")
    return render_template("login.html")


@login_required
@app.route("/logout")
def logout():
    session.clear()
    flash("You are now successfully logged out of your account", "success")
    return redirect(url_for("login"))


@login_required
@app.route("/")
def index():
    return render_template("index.html")


@login_required
@app.route("/monitoring")
def monitoring():
    if session["username"] == "admin":
        url = api_url + "admin"
        response = requests.post(url)
        lambda_info = (json.loads(response.content.decode("utf-8")))
        return render_template("admin.html", task=dict(lambda_info["lambda"]))
    return "<h1>CHEATER!!!!!!!!!!</h1>"


@login_required
@app.route("/tasks")
def list_tasks():
    url = api_url + "list_tasks"
    if session["username"] == "admin":
        url = api_url + "admin"
        response = requests.post(url)
        tasks = (json.loads(response.content.decode("utf-8")))
        print(tasks)
        return render_template("tasks.html", tasks=tasks["tasks"], stop_url=api_url + "stop_task")
    response = requests.post(url, json={"username": session["username"]})

    tasks = (json.loads(response.content.decode("utf-8")))

    return render_template("tasks.html", tasks=tasks, stop_url=api_url + "stop_task")


@login_required
@app.route("/add_task", methods=["GET", "POST"])
def add_task():
    if request.method == "POST":
        url = api_url + "list_tasks"
        response = requests.post(url, json={"username": session["username"]})
        tasks = (json.loads(response.content.decode("utf-8")))
        statuses = []
        results = []
        for i in range(len(tasks)):
            statuses.append(tasks[i]["status"])
            results.append(tasks[i]["duration"])
        counter = 0
        for i in range(len(results)):
            if -1 < statuses[i] < results[i]:
                counter += 2
        if counter > 5:
            flash("Maximum of concurrent tasks is 5! Wait for one to complete")
            redirect(url_for("list_tasks"))
        duration = int(request.form.get("duration"))
        if duration and 30 > duration > 0:
            url = api_url + 'add_task'
            response = requests.post(url, json={"username": session["username"], "duration": duration})
            return redirect(url_for("list_tasks"))
        flash("Minimum duration is 0 and maximum is 30")
        return redirect(url_for("add_task"))
    return render_template("add_task.html")


if __name__ == '__main__':
    app.config.update({
        'TESTING': True
    })
    app.run(debug=True, host='0.0.0.0')
