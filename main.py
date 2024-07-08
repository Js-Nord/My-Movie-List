from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os

MOVIE_API = "https://api.themoviedb.org/3/search/movie"
TOKEN = os.environ.get("TOKEN")

headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {TOKEN}"
}


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

Bootstrap5(app)

# CREATE DB


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///new_movie_list.db'
db.init_app(app)
# CREATE TABLE


class Movie(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(250), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(1000), nullable=True)
    img_url: Mapped[str] = mapped_column(String, nullable=False)

    # IMPORTANT: REMEMBER THAT THE DEFAULT VALUE FOR NULLABLE IS ALWAYS FALSE, SO SET TO TRUE IF YOU WANT IT EMPTY.


class MovieForm(FlaskForm):
    movie = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')


class RatingForm(FlaskForm):
    rating = StringField("Your Rating out of 10 e.g. 7.5", validators=[DataRequired()])
    review = StringField("Your Review", validators=[DataRequired()])
    submit = SubmitField("Done")


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all()
    for num in range(len(all_movies)):
        all_movies[num].ranking = len(all_movies) - num
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/add", methods=["GET", "POST"])
def add():
    form = MovieForm()
    if form.validate_on_submit():
        params = {"query": request.form["movie"]}
        movie_list = requests.get(MOVIE_API, headers=headers, params=params).json()["results"]
        return render_template("select.html", list=movie_list)
    return render_template("add.html", form=form)


@app.route("/select")
def select():
    movie_id = request.args.get("id")
    details_api = f"https://api.themoviedb.org/3/movie/{movie_id}"
    response_details = requests.get(details_api, headers=headers).json()
    new_movie = Movie(
        title=response_details["original_title"],
        year=response_details["release_date"],
        description=response_details["overview"],
        img_url=f"https://image.tmdb.org/t/p/w500{response_details['poster_path']}"
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for("edit"))


@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = RatingForm()
    if form.validate_on_submit():
        result = db.session.execute(db.select(Movie).order_by(Movie.title))
        actual_movie = result.scalar()
        actual_movie.rating = form.rating.data
        actual_movie.review = form.review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", form=form)


@app.route("/delete")
def delete():
    get_movie = request.args.get("id")
    movie_to_delete = db.get_or_404(Movie, get_movie)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for("home"))


if __name__ == '__main__':
    app.run(debug=True)
