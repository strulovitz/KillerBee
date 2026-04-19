"""
forms.py — WTForms for KillerBee
=================================
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SelectField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, Optional, ValidationError


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[
        ('raja', 'Raja Bee — I command Swarms of GiantQueens and DwarfQueens'),
        ('giant_queen', 'Giant Queen — I coordinate DwarfQueens'),
        ('dwarf_queen', 'Dwarf Queen — I coordinate Workers'),
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
    max_queens = IntegerField('Max Queens (GiantQueens + DwarfQueens)', validators=[DataRequired(), NumberRange(min=2, max=100)],
                              default=10)


class JoinSwarmForm(FlaskForm):
    endpoint = StringField('Your Endpoint URL', validators=[DataRequired()],
                           description='e.g. http://192.168.1.100:5000')


_PHOTO_EXTS = ['jpg', 'jpeg', 'png', 'webp']
_AUDIO_EXTS = ['mp3', 'wav', 'm4a', 'ogg', 'flac']
_VIDEO_EXTS = ['mp4', 'mov', 'webm', 'mkv']
_ALL_MEDIA_EXTS = _PHOTO_EXTS + _AUDIO_EXTS + _VIDEO_EXTS


class SubmitJobForm(FlaskForm):
    task = TextAreaField('Task', validators=[DataRequired(), Length(min=10)])
    media_type = SelectField(
        'Media Type',
        choices=[
            ('text',  'Text only'),
            ('photo', 'Photo'),
            ('audio', 'Audio'),
            ('video', 'Video'),
        ],
        default='text',
    )
    media_file = FileField(
        'Media File',
        validators=[
            Optional(),
            FileAllowed(_ALL_MEDIA_EXTS, 'Allowed: jpg/jpeg/png/webp, mp3/wav/m4a/ogg/flac, mp4/mov/webm/mkv'),
        ],
    )

    def validate_media_file(self, field):
        """File is required when media_type is not 'text'."""
        if self.media_type.data != 'text' and not field.data:
            raise ValidationError('A file is required when media type is not Text only.')

        if field.data:
            import os
            ext = os.path.splitext(field.data.filename)[1].lower().lstrip('.')
            mt = self.media_type.data
            if mt == 'photo' and ext not in _PHOTO_EXTS:
                raise ValidationError(f'Photo must be one of: {", ".join(_PHOTO_EXTS)}')
            elif mt == 'audio' and ext not in _AUDIO_EXTS:
                raise ValidationError(f'Audio must be one of: {", ".join(_AUDIO_EXTS)}')
            elif mt == 'video' and ext not in _VIDEO_EXTS:
                raise ValidationError(f'Video must be one of: {", ".join(_VIDEO_EXTS)}')
