from flask import Flask, render_template, url_for, request, redirect, flash
from flask import jsonify, session, make_response, abort
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from functools import wraps
import ast
from database_setup import Base, ISP, Package, User

engine = create_engine("sqlite:///isp.db")
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
db_session = DBSession()

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "ISP List"


def login_required(f):
    """
    Check that that a user is authorized to view the page.
    """
    @wraps(f)
    def decorated_function(**kw):
        if "user_id" not in session:
            flash("You must be logged in make any changes.")
            return redirect(url_for('show_login', next=request.url))

        if request.endpoint == 'edit_isp' or\
           request.endpoint == 'delete_isp' or\
           request.endpoint == 'new_package' or\
           request.endpoint == 'edit_package' or\
           request.endpoint == 'delete_package':
                isp = db_session.query(ISP).filter_by(id=kw["isp_id"]).one()
                if int(session["user_id"]) != isp.user_id:
                    flash("Only the creator can make changes to an ISP!")
                    return redirect("/")

        return f(**kw)
    return decorated_function


@app.before_request
def csrf_protect():
    """
    Check for CSRF token before processing all POST requests except for login
    via oauth.
    """
    if request.endpoint == 'gconnect' or request.endpoint == 'fbconnect':
        return

    if request.method == "POST":
        token = session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            abort(403)


def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = "".\
            join(random.choice(string.ascii_uppercase + string.digits)
                 for x in range(128))
    return session['_csrf_token']


app.jinja_env.globals['csrf_token'] = generate_csrf_token


@app.route("/login/")
def show_login():
    """
    Create a state token to prevent request forgery.
    Store it in the session for later validation.
    """
    state = "".join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    session["state"] = state
    return render_template("login.html", STATE=state, title="Login")


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    provider_uid = credentials.id_token['sub']
    if result['user_id'] != provider_uid:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = session.get('access_token')
    stored_gplus_id = session.get('provider_uid')
    if stored_access_token is not None and provider_uid == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    session['access_token'] = credentials.access_token
    session['provider_uid'] = provider_uid

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    session['provider'] = 'google'
    session['username'] = data['name']
    session['picture'] = data['picture']
    session['email'] = data['email']

    # Create a new user if the user is not already in the database
    print("email = {}".format(session['email']))
    session['user_id'] = get_user_id(session['email'])
    print("User id = {}".format(get_user_id(session['email'])))
    if session['user_id'] is None:
        session['user_id'] = create_user(session)

    output = """
        <h3>Welcome, {}!</h3>
        <img src="{}"
            style = "width: 150px;
                height: 150px;
                border-radius: 80px;
                -webkit-border-radius: 150px;
                -moz-border-radius: 150px;">
    """.format(session['username'], session['picture'])

    flash("You are now logged in as {}".format(session['username'].title()))
    print("done!")
    return output


@app.route('/disconnect/')
def disconnect():
    print("provider: {}".format(session['provider']))
    access_token = session['access_token']
    print('In disconnect access token is {}'.format(access_token))
    print('User name is: ')
    print(session['username'])
    if access_token is None:
        print('Access Token is None')
        response = \
            make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    if session['provider'] == 'google':
        url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
            % session['access_token']
    elif session['provider'] == 'facebook':
        url = 'https://graph.facebook.com/%s/permissions?access_token=%s' \
            % (session['provider_uid'], session['access_token'])

    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print('result is ')
    print(result)
    if result['status'] == '200':
        del session['access_token']
        del session['provider_uid']
        del session['username']
        del session['email']
        del session['picture']
        del session['user_id']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        flash("Logged out successfully.")
        return redirect(url_for("show_isps"))
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route("/")
@app.route("/isps/")
def show_isps():
    """
    This page will show a list of all the ISPs in the database.
    """
    isps = db_session.query(ISP).order_by(ISP.name)
    return render_template(
        "isps.html",
        isps=isps,
        location="home",
        title="ISPs")


@app.route("/isps/new/", methods=["GET", "POST"])
@login_required
def new_isp(**kw):
    """
    This page will be for adding a new ISP to the database.
    """
    if request.method == "POST":
        if request.form["choice"] == "create":
            isp = ISP(name=request.form["name"], user_id=session["user_id"])
            db_session.add(isp)
            db_session.commit()
            flash("New ISP Successfully Created.")
        return redirect(url_for("show_isps"))
    else:
        return render_template("new_isp.html", title="New ISP")


@app.route("/isps/<int:isp_id>/edit/", methods=["GET", "POST"])
@login_required
def edit_isp(isp_id):
    """
    This page will be for editing ISPs in the database.
    """
    isp = db_session.query(ISP).filter_by(id=isp_id).one()

    if request.method == "POST":
        if request.form["choice"] == "edit":
            isp.name = request.form["name"]
            db_session.add(isp)
            db_session.commit()
            flash("ISP Successfully Edited.")
        return redirect(url_for("show_isps"))
    else:
        return render_template("edit_isp.html", isp=isp, title="Edit ISP")


@app.route("/isps/<int:isp_id>/delete/", methods=["GET", "POST"])
@login_required
def delete_isp(isp_id):
    """
    This page will be for deleting ISPs in the database.
    """
    isp = db_session.query(ISP).filter_by(id=isp_id).one()

    if request.method == "POST":
        if request.form["choice"] == "delete":
            db_session.delete(isp)
            db_session.commit()
            flash("ISP Successfully Deleted.")
        return redirect(url_for("show_isps"))
    else:
        return render_template("delete_isp.html", isp=isp, title="Delete ISP")


@app.route("/isps/<int:isp_id>/")
@app.route("/isps/<int:isp_id>/packages/")
def show_packages(isp_id):
    """
    This page will show a list of all the packages offered by the ISP.
    """
    isp = db_session.query(ISP).filter_by(id=isp_id).one()

    packages = db_session.query(Package).filter_by(isp_id=isp_id)\
        .order_by(Package.name)
    return render_template(
        "packages.html",
        isp=isp,
        packages=packages,
        title="Packages")


@app.route("/isps/<int:isp_id>/packages/new/", methods=["GET", "POST"])
@login_required
def new_package(isp_id):
    """
    This page will add a new package to the ISP identified by isp_id.
    """
    isp = db_session.query(ISP).filter_by(id=isp_id).one()

    if request.method == "POST":
        if request.form["choice"] == "create":
            package = Package(
                name=request.form["name"],
                bandwidth=int(request.form["bandwidth"]),
                cap=int(request.form["cap"]),
                price=float(request.form["price"]),
                user_id=session["user_id"],
                isp_id=isp_id)
            db_session.add(package)
            db_session.commit()
            flash("New Package Successfully Created.")

        return redirect(url_for('show_packages', isp_id=isp_id))
    else:
        return render_template(
            "new_package.html",
            isp=isp,
            title="New Package")


@app.route(
    "/isps/<int:isp_id>/packages/<int:package_id>/edit/",
    methods=["GET", "POST"])
@login_required
def edit_package(isp_id, package_id):
    """
    This page will be for editing packages in the database.
    """
    isp = db_session.query(ISP).filter_by(id=isp_id).one()
    package = db_session.query(Package).filter_by(id=package_id).one()

    if request.method == "POST":
        if request.form["choice"] == "edit":
            package.name = request.form["name"]
            package.bandwidth = int(request.form["bandwidth"])
            package.cap = int(request.form["cap"])
            package.price = float(request.form["price"])
            db_session.add(package)
            db_session.commit()
            flash("Package Updated.")

        return redirect(url_for('show_packages', isp_id=isp_id))
    else:
        return render_template(
            "edit_package.html",
            isp=isp,
            package=package,
            title="Edit Package")


@app.route(
    "/isps/<int:isp_id>/packages/<int:package_id>/delete/",
    methods=["GET", "POST"])
@login_required
def delete_package(isp_id, package_id):
    """
    This page will be for deleting packages in the database.
    """
    isp = db_session.query(ISP).filter_by(id=isp_id).one()
    package = db_session.query(Package).filter_by(id=package_id).one()

    if request.method == "POST":
        if request.form["choice"] == "delete":
            db_session.delete(package)
            db_session.commit()
            flash("Package Deleted.")

        return redirect(url_for('show_packages', isp_id=isp_id))
    else:
        return render_template(
            "delete_package.html",
            isp=isp,
            package=package,
            title="Delete Package")


@app.route("/isps/JSON/")
def isps_json():
    """
    JSON API to view isps.
    """
    isps = db_session.query(ISP).order_by(ISP.name).all()
    return jsonify(isp_list=[isp.serialize for isp in isps])


@app.route("/isps/<int:isp_id>/packages/JSON/")
def packages_json(isp_id):
    """
    JSON API to view packages.
    """
    packages = db_session.query(Package).filter_by(isp_id=isp_id)\
        .order_by(Package.name).all()
    return jsonify(package_list=[package.serialize for package in packages])


@app.route("/isps/<int:isp_id>/packages/<int:package_id>/JSON/")
def package_json(isp_id, package_id):
    """
    JSON API to view a package identified by package_id.
    """
    package = db_session.query(Package).filter_by(id=package_id).one()
    return jsonify(pac=package.serialize)


def create_user(session):
    new_user = User(
        name=session["username"],
        email=session["email"],
        picture=session["picture"])
    db_session.add(new_user)
    db_session.commit()

    user = db_session.query(User).filter_by(email=session["email"]).one()
    return user.id


def get_user_info(user_id):
    user = db_session.query(User).filter_by(id=user_id).one()
    return user


def get_user_id(email):
    try:
        user = db_session.query(User).filter_by(email=email).one()
    except NoResultFound:
        print("Creating new user.")
        return None
    return user.id


@app.template_filter("capitalize_words")
def capitalize_word(my_str):
    return my_str.title()


if __name__ == "__main__":
    app.secret_key = "Ut0ndr1agr14*$hi7mh@7ayAk0*"
    app.debug = True
    app.run(host="0.0.0.0", port=8080)
