#!/usr/bin/python2

# Database server setup
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from DBsetup import Base, Category, Item, User

# Web server setup
from flask import(
    Flask,
    render_template,
    request,
    redirect,
    jsonify,
    url_for,
    flash)

# Google login setup
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
from functools import wraps


# Connect to Database and create database session
engine = create_engine('sqlite:///categories.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Webserver
app = Flask(__name__)


# Login ID
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item Catalog"


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(
            json.dumps('Invalid state parameter.'), 401)
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
    url = (
        'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' %
        access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; \
        height: 300px;border-radius: 150px; \
        -webkit-border-radius: 150px; \
        -moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    try:
        user = session.query(User).filter_by(id=user_id).one()
        return user
    except:
        return None


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Authentication Decorator
def loginRequired(f):
    @wraps(f)
    def decoratedFunction(*arg, **kwargs):
        if 'username' not in login_session:
            return redirect('/login')
        return f(*arg, **kwargs)
    return decoratedFunction


# Authorization Decorator
def authorizationRequired(f):
    @wraps(f)
    def decoratedFunction(*arg, **kwargs):
        checkCategory = session.query(Category). \
            filter_by(name=kwargs['category_name']).one()
        if checkCategory.user_id != login_session['user_id']:
            flash('Not your created Category. Access denied !!!')
            return redirect('/catalog')
        return f(*arg, **kwargs)
    return decoratedFunction


# JSON APIs to view Category Information
@app.route(
    '/catalog/<string:category_name>/JSON')
def categoryListJSON(category_name):
    category = session.query(Category). \
        filter_by(name=category_name).one()
    items = session.query(Item). \
        filter_by(name=category.name).all()
    return jsonify(
        ListItem=[i.serialize for i in items])


@app.route(
    '/catalog/<string:category_name>/<string:item_name>/JSON')
def listItemJSON(category_name, item_name):
    List_Item = session.query(Item). \
        filter_by(name=item_name).one()
    return jsonify(
        List_Item=List_Item.serialize)


@app.route('/catalog/JSON')
def categoriesJSON():
    categories = session.query(Category).all()
    return jsonify(
        categories=[r.serialize for r in categories])


# Show all categories
@app.route('/')
@app.route('/catalog')
def showCategories():
    categories = session.query(Category). \
        order_by(asc(Category.name))
    items = session.query(Item).all()
    if 'username' not in login_session:
        return render_template(
            'publiccategories.html',
            categories=categories,
            items=items)
    else:
        return render_template(
            'categories.html',
            categories=categories)


# Create a new category
@app.route('/catalog/new/', methods=['GET', 'POST'])
@loginRequired
def newCategory():
    if request.method == 'POST':
        existedKey = session.query(Category). \
            filter_by(name=request.form['name']).first()
        if not existedKey:
            newCategory = Category(
                name=request.form['name'],
                user_id=login_session['user_id'])
            session.add(newCategory)
            session.commit()
            flash(
                'New Category %s Successfully Created' %
                newCategory.name)
        else:
            flash('Duplicated Category name')
        return redirect(url_for('showCategories'))
    else:
        return render_template('newCategory.html')


# Edit a category
@app.route(
    '/catalog/<string:category_name>/edit/',
    methods=['GET', 'POST'])
@loginRequired
@authorizationRequired
def editCategory(category_name):
    editCategory = session.query(Category). \
        filter_by(name=category_name).one()
    if request.method == 'POST':
        if request.form['button'] == "save":
            if request.form['name']:
                editCategory.name = request.form['name']
                session.commit()
                flash(
                    'Category Successfully Edited %s' %
                    editCategory.name)
        if request.form['button'] == "cancel":
            flash('Canceled')
        return redirect(url_for('showCategories'))
    else:
        return render_template(
            'editCategory.html',
            category=editCategory)


# Delete a category
@app.route(
    '/catalog/<string:category_name>/delete/',
    methods=['GET', 'POST'])
@loginRequired
@authorizationRequired
def deleteCategory(category_name):
    categoryToDelete = session.query(Category). \
        filter_by(name=category_name).one()
    if request.method == 'POST':
        if request.form['button'] == "delete":
            itemsToDelete = session.query(Item). \
                filter_by(category_name=category_name).all()
            for item in itemsToDelete:
                session.delete(item)
            session.delete(categoryToDelete)
            flash(
                '%s Successfully Deleted' %
                categoryToDelete.name)
            session.commit()
        if request.form['button'] == "cancel":
            flash('Canceled')
        return redirect(url_for(
            'showCategories',
            category_name=category_name))
    else:
        return render_template(
            'deleteCategory.html',
            category=categoryToDelete)


# Show a category list
@app.route('/catalog/<string:category_name>/')
def showList(category_name):
    category = session.query(Category). \
        filter_by(name=category_name).one()
    items = session.query(Item). \
        filter_by(category_name=category.name).all()
    return render_template(
        'list.html',
        items=items,
        category=category)


# Create a new list item
@app.route(
    '/catalog/<string:category_name>/new/',
    methods=['GET', 'POST'])
@loginRequired
def newListItem(category_name):
    category = session.query(Category). \
        filter_by(name=category_name).one()
    if request.method == 'POST':
        existedKey = session.query(Item). \
            filter_by(name=request.form['name']).first()
        if not existedKey:
            newItem = Item(
                name=request.form['name'],
                description=request.form['description'],
                category_name=category.name)
            session.add(newItem)
            session.commit()
            flash(
                'New Item: %s Successfully Created' %
                (newItem.name))
        else:
            flash('Duplicated Item name')
        return redirect(url_for(
            'showList',
            category_name=category_name))
    else:
        return render_template(
            'newListItem.html',
            category_name=category_name)


# Edit a list item
@app.route(
    '/catalog/<string:category_name>/<string:item_name>/edit',
    methods=['GET', 'POST'])
@loginRequired
@authorizationRequired
def editListItem(category_name, item_name):
    editedItem = session.query(Item). \
        filter_by(name=item_name).one()
    category = session.query(Category). \
        filter_by(name=category_name).one()
    if request.method == 'POST':
        if request.form['button'] == "save":
            if request.form['name']:
                editedItem.name = request.form['name']
            if request.form['description']:
                editedItem.description = request.form['description']
            session.add(editedItem)
            session.commit()
            flash('Item Successfully Edited')
        if request.form['button'] == "cancel":
            flash('Canceled')
        return redirect(url_for(
            'showList',
            category_name=category_name))
    else:
        return render_template(
            'editListItem.html',
            category_name=category_name,
            item_name=item_name,
            item=editedItem)


# Delete a list item
@app.route(
    '/catalog/<string:category_name>/<string:item_name>/delete',
    methods=['GET', 'POST'])
@loginRequired
@authorizationRequired
def deleteListItem(category_name, item_name):
    category = session.query(Category). \
        filter_by(name=category_name).one()
    itemToDelete = session.query(Item). \
        filter_by(name=item_name).one()
    if request.method == 'POST':
        if request.form['button'] == "delete":
            session.delete(itemToDelete)
            session.commit()
            flash('Menu Item Successfully Deleted')
        if request.form['button'] == "cancel":
            flash('Canceled')
        return redirect(url_for(
            'showList',
            category_name=category_name))
    else:
        return render_template(
            'deleteListItem.html',
            item=itemToDelete)


# main
if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
