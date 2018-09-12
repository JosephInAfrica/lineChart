from flask import Flask

from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField
from wtforms.validators import DataRequired

app=Flask(__name__)
app.config['SECRET_KEY']='hard to guess'

class nameForm(FlaskForm):
	name=StringField('input a name')
	submit=SubmitField('Submit')

a=nameForm()

if __name__=='__main__':
	app.run()