###############################
####### SETUP (OVERALL) #######
###############################

## Import statements
# Import statements
import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField # Note that you may need to import more here! Check out examples that do what you want to figure out what.
from wtforms.validators import Required # Here, too
from flask_sqlalchemy import SQLAlchemy
import psycopg2
import requests
import json

## App setup code
app = Flask(__name__)
app.debug = True
app.use_reloader = True

## All app.config values

## Statements for db setup (and manager setup if using Manager)
app.config['SECRET_KEY'] = 'hard to guess string from si364'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/aslabot364midterm'
## Provided:
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app) # For database use

global loggedIn
loggedIn = False

global currentUID
currentUID = -1


######################################
######## HELPER FXNS (If any) ########
######################################

def fillCities():
    db.session.add(Cities(name="DETROIT", latitude=44.761527, longitude=-69.322662))
    db.session.add(Cities(name="NEW YORK", latitude=40.7127837, longitude=-74.0059413))
    db.session.add(Cities(name="LOS ANGELES", latitude=34.0522342, longitude=-118.2436849))
    db.session.add(Cities(name="CHICAGO", latitude=41.8781136, longitude=-87.6297982))
    db.session.add(Cities(name="HOUSTON", latitude=29.7604267, longitude=-95.3698028))
    db.session.add(Cities(name="PHILADELPHIA", latitude=39.9525839, longitude=-75.1652215))
    db.session.add(Cities(name="PHOENIX", latitude=33.4483771, longitude=-112.0740373))
    db.session.add(Cities(name="SAN ANTONIO", latitude=29.4241219, longitude=-98.4936281))
    db.session.add(Cities(name="SAN DIEGO", latitude=32.715738, longitude=-117.1610838))
    db.session.add(Cities(name="DALLAS", latitude=32.7766642, longitude=-96.79698789999999))
    db.session.add(Cities(name="SAN JOSE", latitude=37.3382082, longitude=-121.8863286))
    db.session.add(Cities(name="AUSTIN", latitude=30.267153, longitude=-97.7430608))
    db.session.add(Cities(name="INDIANAPOLIS", latitude=39.768403, longitude=-86.158068))
    db.session.add(Cities(name="COLUMBUS", latitude=39.9611755, longitude=-82.99879419999999))
    db.session.add(Cities(name="CHARLOTTE", latitude=35.2270869, longitude=-80.8431267))
    db.session.add(Cities(name="FORT WORTH", latitude=32.7554883, longitude=-97.3307658))
    db.session.commit()


##################
##### MODELS #####
##################

class Users(db.Model):
    __tablename__ = "Users"
    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True)
    password = db.Column(db.String(20))
    cities = db.relationship("FavoritedCities", backref="Users")
    activities = db.relationship("Activities", backref="Users")
    clothing = db.relationship("Clothing", backref="Users")


class Activities(db.Model):
    __tablename__ = "Activities"
    uid = db.Column(db.Integer, db.ForeignKey(Users.uid), primary_key=True)
    activity = db.Column(db.String(30), primary_key=True)

class Clothing(db.Model):
    __tablename__ = "Clothing"
    uid = db.Column(db.Integer, db.ForeignKey(Users.uid), primary_key=True)
    clothingType = db.Column(db.String(30), primary_key=True)
    lowestTemp = db.Column(db.Integer)
    highestTemp = db.Column(db.Integer)

class Cities(db.Model):
    __tablename__ = "Cities"
    cid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25), nullable=False, unique=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    favoritedCities = db.relationship("FavoritedCities", backref="Cities")

class FavoritedCities(db.Model):
    __tablename__ = "FavoritedCities"
    uid = db.Column(db.Integer, db.ForeignKey(Users.uid), primary_key=True)
    cid = db.Column(db.Integer, db.ForeignKey(Cities.cid), primary_key=True)

###################
###### FORMS ######
###################

def noSpecialCharacters(form, field):
    if '!' in field.data or '@' in field.data or '#' in field.data or \
       '$' in field.data or '%' in field.data or '^' in field.data or \
       '&' in field.data or '*' in field.data or '(' in field.data or \
       '-' in field.data:
        raise ValidationError('Field must not contain special characters')

def nodupClothing(form, field):
    q = Clothing.query.filter_by(uid=currentUID).filter_by(clothingType=field).first()
    if q:
        raise ValidationError('Duplicate entry')

class LoginForm(FlaskForm):
    username = StringField("Username: ",validators=[Required()])
    password = PasswordField("Password: ",validators=[Required(), noSpecialCharacters])
    submit = SubmitField("Log in")
    createAccount = SubmitField("Create account")

class ClothingForm(FlaskForm):
    articleClothing = SelectField("Select an article of clothing: ", choices=[('tank top','Tank Top'),('sweater','Sweater'),('jacket','Jacket'),('coat','Coat')], validators=[Required(), nodupClothing])
    lowTemp = IntegerField("Low: ", validators=[Required()])
    highTemp = IntegerField("High: ", validators=[Required()])
    submit = SubmitField("Submit")

class CityForm(FlaskForm):
    city = SelectField("Select a favorite city: ", validators=[Required()])
    submit = SubmitField("Submit")

class InfoForm(FlaskForm):
    favoriteCities = SelectField("Favorite cities: ", validators=[Required()])
    submit = SubmitField("Get Info")
    logout = SubmitField("Log Out")


#######################
###### VIEW FXNS ######
#######################

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    global loggedIn
    global currentUID
    form = LoginForm()
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if form.submit.data:
            q = Users.query.filter_by(username=username).filter_by(password=password).first()
            if not q:
                flash('Wrong username or password')
                return redirect(url_for('login'))
            else:
                currentUID = q.uid
                loggedIn = True
                return redirect(url_for('info'))
        elif form.createAccount.data:
            q = Users.query.filter_by(username=username).first()
            if q:
                flash('user already exists')
                return redirect(url_for('login'))
            else:
                user = Users(username=username, password=password)
                db.session.add(user)
                db.session.commit()
                return redirect(url_for('login'))

    return render_template('login.html', form=form)

@app.route('/info', methods=['GET', 'POST'])
def info():
    global loggedIn
    global currentUID
    if not loggedIn:
        return redirect(url_for('login'))
    form = InfoForm()
    iter = FavoritedCities.query.filter_by(uid=currentUID).all()
    form.favoriteCities.choices = [(Cities.query.filter_by(cid=row.cid).first().cid, Cities.query.filter_by(cid=row.cid).first().name) for row in FavoritedCities.query.filter_by(uid=currentUID).all()]
    suggestion1 = None
    suggestion2 = None
    if not FavoritedCities.query.filter_by(uid=currentUID).first():
        suggestion1 = "Click here to set your favorite cities!"
    if not Clothing.query.filter_by(uid=currentUID).first():
        suggestion2 = "Click here to set your clothing preferences!"
    if request.method == 'POST':
        base_url = "https://api.darksky.net/forecast/37f3f52d76a1699428512298c4ec2055/"
        choice = request.form['favoriteCities']
        print("Choice: " + str(choice))
        city = Cities.query.filter_by(cid=choice).first()
        print(type(city))
        longitude = city.longitude
        latitude = city.latitude
        ext = str(latitude) + "," + str(longitude)
        url = base_url + ext
        req = requests.get(url)
        if not req:
            page_not_found()
        json_data = json.loads(req.text)
        response = json_data#['results']
        temp = response["currently"]["temperature"]
        clothing_t = Clothing.query.filter_by(uid=currentUID).filter(Clothing.lowestTemp<=temp).filter(Clothing.highestTemp>=temp).first()
        if clothing_t:
            clothing = clothing_t.clothingType
        else:
            clothing = "No applicable clothing item"

        favCities = FavoritedCities.query.filter_by(uid=currentUID).all()
        temperatures = []
        for city in favCities:
            print("here")
            city1 = Cities.query.filter_by(cid=city.cid).first()
            latitude, longitude = city1.latitude, city1.longitude
            ext = str(latitude) + "," + str(longitude)
            url = base_url + ext
            req = requests.get(url)
            if not req:
                page_not_found()
            json_data = json.loads(req.text)
            response = json_data#['results']
            temp = response['currently']['temperature']
            temperatures.append((city1.name, temp))
        return render_template('info.html', form=form, temperatures=temperatures, clothing=clothing)
    return render_template('info.html', form=form, temperatures=[], clothing=None, suggestion1=suggestion1, suggestion2=suggestion2)


@app.route('/add-city', methods=['GET', 'POST'])
def addCity():
    global loggedIn
    global currentUID
    form = CityForm()
    form.city.choices = [(row.cid, row.name) for row in Cities.query.all()]
    if not loggedIn:
        return redirect(url_for('login'))
    if request.method == 'POST':
        city = request.form['city']
        #print(city)
        c = Cities.query.filter_by(cid=city).first()
        favCityEntry = FavoritedCities(uid=currentUID, cid=c.cid)
        db.session.add(favCityEntry)
        db.session.commit()
        return redirect(url_for('addCity'))

    return render_template('addCity.html', form=form)

@app.route('/add-clothing', methods=['GET', 'POST'])
def addClothing():
    global loggedIn
    global currentUID
    form = ClothingForm()

    if not loggedIn:
        return redirect(url_for('login'))

    if request.method == 'POST':
        articleClothing = request.form['articleClothing']
        lowestTemp = request.form['lowTemp']
        highestTemp = request.form['highTemp']
        clothingEntry = Clothing(uid=currentUID, clothingType=articleClothing, lowestTemp=lowestTemp, highestTemp=highestTemp)
        db.session.add(clothingEntry)
        db.session.commit()
        return redirect(url_for('addClothing'))

    return render_template('addClothing.html', form=form)

@app.route("/logout")
def logout():
    global loggedIn
    loggedIn = False
    global currentUID
    currentUID = -1
    return redirect(url_for('home'))


## Code to run the application...

# Put the code to do so here!
# NOTE: Make sure you include the code you need to initialize the database structure when you run the application!

if __name__ == "__main__":
    db.create_all() # Will create any defined models when you run the application
    app.run() # The usual
    if not Cities.query.all():
        fillCities()