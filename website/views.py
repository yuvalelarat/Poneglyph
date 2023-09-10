import io, os
from flask import Flask, Blueprint, render_template, flash, request, redirect, url_for, send_file, Response, make_response
from stegano import lsb
from PIL import Image
from flask_login import login_required, current_user
from .models import User,File
from .auth import *
from sqlalchemy.exc import SQLAlchemyError
from . import views, db, actions
import base64


views = Blueprint('views', __name__)

@views.route('/')
def home():
    return render_template("home.html", user=current_user)

@views.route('/encode', methods=['GET', 'POST'])
@login_required
def encode():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        text = request.form.get('text')
        filename = request.form.get('filename')

        if uploaded_file and text:
            # Error handling in case the user upload's wrong format!!!!!!!!
            try: 
                img = lsb.hide(uploaded_file, text)

                img_buffer = io.BytesIO()
                img.save(img_buffer, format='PNG')  

                new_file = File(
                    name=filename,
                    data=img_buffer.getvalue(),
                    user_id=current_user.id,
                    text=text,
                    author = current_user.userName,
                    sent_by = None,
                )
                db.session.add(new_file)
                db.session.commit()

                response = Response(img_buffer.getvalue(), content_type='image/png')
                response.headers['Content-Disposition'] = f'attachment; filename="{filename}.PNG"'

                return response
            except:
                flash('File format error, please provide one of following formats - png, jpg, jpeg.', category='error')
                
    return render_template("encode.html", user=current_user)

@views.route('/decode' , methods=['GET', 'POST'])
@login_required
def decode():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        
        if uploaded_file:
            try:
                decoded_text = lsb.reveal(uploaded_file)
                return render_template("decode.html", user=current_user, decoded_text=decoded_text)
            except IndexError: 
                # If lsb.reveal gets no encryption in file
                flash('No decoded text in file or unsupported image!', category='error')      
    return render_template("decode.html", user=current_user)

@views.route('/files/<string:username>', methods=["GET", "POST"])
@login_required
def user_files(username):
    if username != current_user.userName:
        flash('Unauthorized', category='error') 
        return render_template("home.html" ,user=current_user)
    
    user = current_user
    files = File.query.filter_by(user_id=user.id).all()

    file_data = []
    for file in files:
        file_data.append({
            'id': file.id,
            'name': file.name,
            'date': file.date,
            'text': file.text,
            'data_base64': base64.b64encode(file.data).decode('utf-8'), #Encode the image data
            'author':file.author,
            'sent_by':file.sent_by
        })

    return render_template('files.html', files=file_data, user=current_user)