from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import config

IMG_PATH = "https://image.tmdb.org/t/p/w500"

'''
Red underlines? Install the required packages first: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from requirements.txt for this project.
'''

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movies.db"
Bootstrap5(app)
db = SQLAlchemy()
db.init_app(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


with app.app_context():
    db.create_all()


class MovieForm(FlaskForm):
    rating = StringField('Your Rating Out of 10 e.g. 7.5', validators=[DataRequired()])
    review = StringField('Your review', validators=[DataRequired()])
    submit = SubmitField('Done')


class MovieTitle(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')


@app.route("/")
def home():
    all_movies = db.session.execute(db.select(Movie).order_by(Movie.rating)).scalars().all()

    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()

    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = MovieForm()
    movie_id = request.args.get('id')
    movie_to_edit = db.session.execute(db.select(Movie).where(Movie.id == movie_id)).scalar()

    if request.method == 'POST':
        if form.validate_on_submit():
            # UPDATE RECORD
            movie_to_edit.rating = float(form.rating.data)
            movie_to_edit.review = form.review.data
            db.session.commit()
            return redirect(url_for('home'))

    return render_template("edit.html", form=form, movie=movie_to_edit)


@app.route("/delete")
def delete():
    movie_id = request.args.get('id')
    movie_to_delete = db.get_or_404(Movie, movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=["GET", "POST"])
def add():
    form = MovieTitle()
    if request.method == "POST":
        if form.validate_on_submit():
            movie_to_add = form.title.data
            url = f"https://api.themoviedb.org/3/search/movie?query={movie_to_add}&include_adult=false&language=en-US&page=1"
            headers = {
                "accept": "application/json",
                "Authorization": f"Bearer {config.API_KEY}"
            }
            response = requests.get(url, headers=headers).json()

            movie = response['results']

            return render_template("select.html", movies=movie)
    return render_template("add.html", form=form)


@app.route("/populate")
def populate():
    movie_id = request.args.get('id')
    url = (f"https://api.themoviedb.org/3/movie/{movie_id}?language=en-US")
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {config.API_KEY}"
    }
    response = requests.get(url, headers=headers).json()

    img_url = IMG_PATH + response['poster_path']
    title = response['title']
    year = response['release_date'].split("-")[0]
    description = response['overview']

    new_movie = Movie(
        title=title,
        year=year,
        description=description,
        img_url=img_url,
    )
    db.session.add(new_movie)
    db.session.commit()

    return redirect(url_for('edit', id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True, port=5001)
