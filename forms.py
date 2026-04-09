"""
forms.py — WTForms for KillerBee
=================================
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[
        ('raja', 'Raja Bee — I command Swarms of Queens'),
        ('queen', 'Queen Bee — I run a hive of Workers'),
        ('worker', 'Worker Bee — I contribute my computer'),
        ('beekeeper', 'Beekeeper — I submit tasks'),
    ], validators=[DataRequired()])


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])


class CreateSwarmForm(FlaskForm):
    name = StringField('Swarm Name', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Description')
    raja_model = StringField('RajaBee Model', validators=[DataRequired()],
                             default='llama3.2:3b')
    specialty = SelectField('Specialty', choices=[
        ('general', 'General Purpose'),
        ('coding', 'Code Generation'),
        ('research', 'Research & Analysis'),
        ('creative', 'Creative Writing'),
        ('translation', 'Translation'),
    ], validators=[DataRequired()])
    max_queens = IntegerField('Max Queens', validators=[DataRequired(), NumberRange(min=2, max=100)],
                              default=10)


class JoinSwarmForm(FlaskForm):
    endpoint = StringField('Your Endpoint URL', validators=[DataRequired()],
                           description='e.g. http://192.168.1.100:5000')


class SubmitJobForm(FlaskForm):
    task = TextAreaField('Task', validators=[DataRequired(), Length(min=10)])
