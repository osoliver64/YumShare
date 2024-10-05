import os
import datetime

from cs50 import SQL
from flask import Flask, redirect, render_template, request, session, send_from_directory, url_for
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField
from flask_uploads import UploadSet, IMAGES, configure_uploads
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, password_check

# Configure application
app = Flask(__name__)

# may need to add: app.confi["SECRET_KEY"] = "RANDOM-KEYojoskjdasbkjsbhfoiue"
# destination photos will be uploaded to
app.config["UPLOADED_PHOTOS_DEST"] = "uploads"
app.config["SECRET_KEY"] = "n94r83yd9hun9udh479802912u3g"
# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# UploadSet is a collection of files and we can use its save() method to save uploaded files
photos = UploadSet("photos", IMAGES)
# This funtion [configure_uploads()] will go though all UploadSets and get their configuration and store their configuration on the app
# the first argument is our app and the second one is the photos variable
configure_uploads(app, photos)

class UploadForm(FlaskForm):
    photo = FileField(
        validators=[
            FileAllowed(photos, "Please only upload images"),
            FileRequired("File field should not be empty")
        ]
    )
    submit = SubmitField("Upload")

db = SQL("sqlite:///recipes.db")

# Ensure that the client always receives a fresh response from the server, without relying on cached data
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
@login_required
def index():
    session["sort"] = "nto"
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("Must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("Must provide password")

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )
        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("Invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        confirmation = request.form.get("confirmation")
        if not username:
            return apology("Please enter a username")
        elif db.execute("SELECT * FROM users WHERE username = ?", username):
            return apology("Username already taken")
        elif not first_name:
            return apology("Please enter a first name")
        elif not password:
            return apology("Please enter a password")
        elif password != confirmation:
            return apology("Passwords do not match")
        pass_check = password_check(password)
        
        if pass_check["password_ok"] == True: 
            hash = generate_password_hash(password)
            db.execute("INSERT INTO users(username, hash, first_name) VALUES(?, ?, ?)", username, hash, first_name)
            if last_name:
                db.execute("UPDATE users SET last_name = ? WHERE username = ?", last_name, username)
            dict_id = db.execute("SELECT id FROM users WHERE username = ?", username)
            session["user_id"] = dict_id[0]["id"]
            db.execute("INSERT INTO profile(user_id) VALUES(?)", dict_id[0]["id"])
        
            return redirect("/")
        else:
            first = False
            return render_template("register.html", pass_check=pass_check, first=first)
    first = True
    pass_check = None
    return render_template("register.html",pass_check=pass_check, first=first)


@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():

    if request.method == "POST":
        old_real = db.execute("SELECT hash FROM users WHERE id = ?", session["user_id"])[0]["hash"]
        old = request.form.get("old")
        new = request.form.get("new")
        confirm = request.form.get("confirm")

        if not check_password_hash(old_real, old):
            return apology("Incorrect old password")
        elif not new == confirm:
            return apology("Passwords do not match")
         
        pass_check = password_check(new)
        
        if pass_check["password_ok"] == True:
            new_hash = generate_password_hash(new)
            db.execute("UPDATE users SET hash = ? WHERE id = ?", new_hash, session["user_id"])
        else:
            first = False
            return render_template("change_password.html", pass_check=pass_check, first=first)
        return redirect("/")
    
    first = True
    pass_check = None
    return render_template("change_password.html", first=first, pass_check=pass_check)


@app.route("/my_recipes")
@login_required
def my_recipes():
    return render_template("my_recipes.html")

@app.route("/add_recipe", methods=["GET", "POST"])
@login_required
def add_recipe():
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        ingredients = request.form.get("ingredients")
        inst = request.form.get("inst")
        servings = request.form.get("servings")
        prep = request.form.get("prep")
        cook = request.form.get("cook")
        category = request.form.get("category")
        dt = datetime.datetime.now()
        uploadDateTime = dt.strftime("%Y-%m-%d %H:%M:%S")
        
        notes = request.form.get("notes")
        if not name:
            return apology("please provide a name for your recipe")
        elif not ingredients:
            return apology("please provide ingredients for you recipe")
        elif not inst:
            return apology("please provide instructions for your recipe")
           
        db.execute("INSERT INTO recipes(user_id, name, ingredients, instructions, datetime) VALUES (?, ?, ?, ?, ?)", session["user_id"], name, ingredients, inst, str(uploadDateTime))
        if description:
            db.execute("UPDATE recipes SET description = ? WHERE name = ? AND user_id = ? AND ingredients = ? AND instructions = ?", description, name, session["user_id"], ingredients, inst)
        if notes:
            db.execute("UPDATE recipes SET notes = ? WHERE name = ? AND user_id = ? AND ingredients = ? AND instructions = ?", notes, name, session["user_id"], ingredients, inst)
        if servings:
            db.execute("UPDATE recipes SET servings = ? WHERE name = ? AND user_id = ? AND ingredients = ? AND instructions = ?", servings, name, session["user_id"], ingredients, inst)
        if prep:
            db.execute("UPDATE recipes SET prep = ? WHERE name = ? AND user_id = ? AND ingredients = ? AND instructions = ?", prep, name, session["user_id"], ingredients, inst)
        if cook:
            db.execute("UPDATE recipes SET cook = ? WHERE name = ? AND user_id = ? AND ingredients = ? AND instructions = ?", cook, name, session["user_id"], ingredients, inst)
        if category:
            rec_id = db.execute("SELECT id FROM recipes WHERE user_id = ? AND ingredients = ? AND instructions = ?", session["user_id"], ingredients, inst)[0]["id"]
            db.execute("INSERT INTO rec_cat (rec_id, cat_id, user_id) VALUES (?, ?, ?)", rec_id, category, session["user_id"])

        return redirect("/all_recipes")
    
    categories = db.execute("SELECT id, name FROM categories WHERE user_id = ?", session["user_id"])
    return render_template("add_recipe.html", categories=categories)


@app.route("/all_recipes", methods=["GET", "POST"])
@login_required
def all_recipes():
    if request.method == "POST":
        
        if request.form.get("add_recipe") == "clicked":
            return redirect("/add_recipe")
        
        if not session["sort"] == request.form.get("sort"):
            session["sort"] = request.form.get("sort")
            return redirect("/all_recipes")
        
        recipe_name = request.form["recipe-btn"]
        if recipe_name:
            recipe = db.execute("SELECT id FROM recipes WHERE name = ? AND user_id = ?", recipe_name, session["user_id"])[0]
            session["recipe_id"] = recipe["id"]
            return redirect("/recipe_page")
        else:
            return redirect("/all_recipes")
        
    sort = session["sort"]
    if sort == "otn":
        recipes = db.execute("SELECT name, image FROM recipes WHERE user_id = ? ORDER BY datetime", session["user_id"])
    elif sort == "alpha":
        recipes = db.execute("SELECT name, image FROM recipes WHERE user_id = ? ORDER BY name", session["user_id"])   
    else:
        recipes = db.execute("SELECT name, image FROM recipes WHERE user_id = ? ORDER BY datetime DESC", session["user_id"])
    return render_template("all_recipes.html", recipes=recipes, sort=sort)


@app.route("/recipe_page", methods=["GET", "POST"])
@login_required
def recipe_page():
    if request.method == "POST":
        image = db.execute("SELECT image FROM recipes WHERE id = ? AND user_id = ?", session["recipe_id"], session["user_id"])[0]["image"]
        if not image == "/static/images/default-recipe.jpg":
            os.remove(f".{image}")
        db.execute("DELETE FROM rec_cat WHERE rec_id = ? AND user_id = ?", session["recipe_id"], session["user_id"])
        db.execute("DELETE FROM recipes WHERE id = ? AND user_id = ?", session["recipe_id"], session["user_id"])
        return redirect("/all_recipes")

    recipe_id = session["recipe_id"]
    recipe = db.execute("SELECT * FROM recipes WHERE id = ?", recipe_id)[0]
    if db.execute("SELECT name FROM categories WHERE id = (SELECT cat_id FROM rec_cat WHERE rec_id = ?)", recipe_id):
        category = db.execute("SELECT name FROM categories WHERE id = (SELECT cat_id FROM rec_cat WHERE rec_id = ?)", recipe_id)[0]["name"]
    else:
        category = None
    total = int(recipe["prep"]) + int(recipe["cook"])
    session["upload_type"] = "recipe"
    return render_template("recipe.html", recipe=recipe, total=total, recipe_id=recipe_id, category=category)


@app.route("/profile")
@login_required
def profile():
    session["upload_type"] = "profile"
    profile = db.execute("SELECT * FROM profile WHERE user_id = ?", session["user_id"])[0]
    usernames = db.execute("SELECT first_name, last_name, username FROM users WHERE id = ?", session["user_id"])[0]
    return render_template("profile.html", profile=profile, usernames=usernames)


@app.route("/uploads/<filename>")
def get_file(filename):
    return send_from_directory(app.config["UPLOADED_PHOTOS_DEST"], filename)

@app.route("/upload_image", methods=["GET", "POST"])
@login_required
def upload_image():
    form = UploadForm()
    # If submited and valid, save the photo
    if form.validate_on_submit():
        filename = photos.save(form.photo.data)
        file_url = url_for("get_file", filename=filename) 
        if session["upload_type"] == "profile":
            image = db.execute("SELECT picture FROM profile WHERE user_id = ?", session["user_id"])[0]["picture"]
            if not image == "static/images/default-pfp.jpg":
                os.remove(f".{image}")
            db.execute("UPDATE profile SET picture = ? WHERE user_id = ?", file_url, session["user_id"])
        else:
            image = db.execute("SELECT image FROM recipes WHERE user_id = ? AND id = ?", session["user_id"], session["recipe_id"])[0]["image"]
            if not image == "/static/images/default-recipe.jpg":
                os.remove(f".{image}")
            db.execute("UPDATE recipes SET image = ? WHERE id = ?", file_url, session["recipe_id"])
    else:
        file_url = None
    upload_type = session["upload_type"]
    return render_template("upload_image.html", form=form, file_url=file_url, upload_type=upload_type)


@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        bio = request.form.get("bio")
        favorite_food = request.form.get("favorite_food")
        country = request.form.get("country")

        if bio:
            db.execute("UPDATE profile SET bio = ? WHERE user_id = ?", bio, session["user_id"])
        if favorite_food:
            db.execute("UPDATE profile SET favorite_food = ? WHERE user_id = ?", favorite_food, session["user_id"])
        if country:
            db.execute("UPDATE profile SET country = ? WHERE user_id = ?", country, session["user_id"])
        return redirect("/profile")
    profile = db.execute("SELECT * FROM profile WHERE user_id = ?", session["user_id"])[0]
    return render_template("edit_profile.html", profile=profile)

@app.route("/edit_recipe", methods=["GET", "POST"])
@login_required
def edit_recipe():
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        ingredients = request.form.get("ingredients")
        instructions = request.form.get("inst")
        notes = request.form.get("notes")
        servings = request.form.get("servings")
        prep = request.form.get("prep")
        cook = request.form.get("cook")
        category = request.form.get("category")

        if name:
            db.execute("UPDATE recipes SET name = ? WHERE id = ?", name, session["recipe_id"])
        else:
            return apology("Your recipe must have a name")
        if description:
            db.execute("UPDATE recipes SET description = ? WHERE id = ?", description, session["recipe_id"])
        if ingredients:
            db.execute("UPDATE recipes SET ingredients = ? WHERE id = ?", ingredients, session["recipe_id"])
        else: 
            return apology("Your recipe must contain ingredients")
        if instructions:
            db.execute("UPDATE recipes SET instructions = ? WHERE id = ?", instructions, session["recipe_id"])
        else:
            return apology("Your recipe must contain ingredients")
        if notes:
            db.execute("UPDATE recipes SET notes = ? WHERE id = ?", notes, session["recipe_id"])
        if servings:
            db.execute("UPDATE recipes SET servings = ? WHERE id = ?", servings, session["recipe_id"])
        if prep:
            db.execute("UPDATE recipes SET prep = ? WHERE id = ?", prep, session["recipe_id"])
        if cook:
            db.execute("UPDATE recipes SET cook = ? WHERE id = ?", cook, session["recipe_id"])
        if category:
            if db.execute("SELECT id FROM rec_cat WHERE rec_id = ? AND user_id = ?", session["recipe_id"], session["user_id"]):
                db.execute("UPDATE rec_cat SET cat_id = ? WHERE rec_id = ? AND user_id = ?", category, session["recipe_id"], session["user_id"])
            else:
                db.execute("INSERT INTO rec_cat (cat_id, rec_id, user_id) VALUES (?, ?, ?)", category, session["recipe_id"], session["user_id"])
        return redirect("/recipe_page")

    categories = db.execute("SELECT name, id FROM categories WHERE user_id = ?", session["user_id"])
    if db.execute("SELECT id FROM rec_cat WHERE user_id = ? AND rec_id = ?", session["user_id"], session["recipe_id"]):
        cat = db.execute("SELECT id FROM rec_cat WHERE user_id = ? AND rec_id = ?", session["user_id"], session["recipe_id"])[0]["id"]
    else:
        cat = None
    recipe = db.execute("SELECT * FROM recipes WHERE id = ?", session["recipe_id"])[0]
    return render_template("edit_recipe.html", recipe=recipe, categories=categories, cat=cat)


@app.route("/categories", methods=["GET", "POST"])
@login_required
def categories():
    if request.method == "POST":
        add_cat = request.form.get("add_cat")
        if add_cat == "8392uebdgb287gdb3e8d823ubd973g79eufvb894ubf39u4u934g72082g7233ye38h8d2hijd98ehd9ewh00284hrf971548451951914151":
            return redirect("/add_category")
        catName = request.form.get("catBtn")
        category = db.execute("SELECT id FROM categories WHERE name = ? AND user_id = ?", catName, session["user_id"])[0]
        session["category"] = category["id"]
        return redirect("/category_page")
        
    categories = db.execute("SELECT * FROM categories WHERE user_id = ?", session["user_id"])
    return render_template("categories.html", categories=categories)


@app.route("/add_category", methods=["GET", "POST"])
@login_required
def add_category():
    if request.method == "POST":
        new_cat = request.form.get("name")
        db.execute("INSERT INTO categories (user_id, name) VALUES (?, ?)", session["user_id"], new_cat)
        return redirect("/categories")

    return render_template("add_category.html")

@app.route("/category_page")
@login_required
def category_page():
    category = db.execute("SELECT name FROM categories WHERE user_id = ? AND id = ?", session["user_id"], session["category"])[0]
    recipes = db.execute("SELECT name, image FROM recipes WHERE id IN (SELECT rec_id FROM rec_cat WHERE user_id = ? AND cat_id = ?)", session["user_id"], session["category"])
    return render_template("category_page.html", category=category, recipes=recipes)


@app.route("/rec_cat", methods=["GET", "POST"])
@login_required
def rec_cat():
    if request.method == "POST":
        rec_id = request.form.get("rec")
        if db.execute("SELECT * FROM rec_cat WHERE rec_id = ? AND user_id = ?", rec_id, session["user_id"]):
            db.execute("UPDATE rec_cat SET cat_id = ? WHERE rec_id = ? AND user_id = ?", session["category"], rec_id, session["user_id"])
        else:
            db.execute("INSERT INTO rec_cat (user_id, cat_id, rec_id) VALUES (?, ?, ?)", session["user_id"], session["category"], rec_id)
        return redirect("/category_page")

    recipesAvailable = db.execute("SELECT name, image, id FROM recipes WHERE id NOT IN (SELECT rec_id FROM rec_cat WHERE cat_id = ?) AND user_id = ? ORDER BY datetime DESC", session["category"], session["user_id"])
    category = db.execute("SELECT name FROM categories WHERE id = ?", session["category"])[0]
    return render_template("rec_cat.html", recipesAvailable=recipesAvailable, category=category)