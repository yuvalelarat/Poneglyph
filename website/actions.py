import io
from flask import Flask, Blueprint, render_template, flash, request, redirect, url_for, send_file, Response, make_response
from flask_login import login_required, current_user
from .models import User,File
from sqlalchemy.exc import SQLAlchemyError
from . import views, db

actions = Blueprint('actions', __name__)


@actions.route('/delete_file/<int:file_id>', methods=['GET'])
@login_required
def delete_file(file_id):
    file_to_delete = File.query.get_or_404(file_id)
    
    # Check if the logged-in user owns the file before deleting
    if file_to_delete.user_id == current_user.id:
        db.session.delete(file_to_delete)
        db.session.commit()
    
    return redirect(url_for('views.user_files', username=current_user.userName))

@actions.route('/download_file/<int:file_id>', methods=['GET'])
@login_required
def download_file(file_id):
    file_to_download = File.query.get_or_404(file_id)
    
    img_buffer = io.BytesIO(file_to_download.data)
    
    response = make_response(img_buffer.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename="{file_to_download.name}.PNG"'
    
    return response

@actions.route('/send_file/<int:file_id>', methods=['POST'])
@login_required
def send_file(file_id):
    recipient_username = request.form.get('recipient_username')
    file_to_send = File.query.get_or_404(file_id)
    
    if not recipient_username:
        flash("Please provide a username if you want to send it to someone.", category='error')
        return redirect(url_for('views.user_files', username=current_user.userName))
    
    recipient = User.query.filter_by(userName=recipient_username).first()
    
    if not recipient:
        flash("No user with the provided username.", category='error')
        return redirect(url_for('views.user_files', username=current_user.userName))
    
    
    new_file = File(
        name=file_to_send.name,
        data=file_to_send.data,
        text=file_to_send.text,
        user_id=recipient.id,
        author=file_to_send.author,
        sent_by=current_user.userName,
    )

    
    db.session.add(new_file)
    db.session.commit()
    
    flash(f"File sent to {recipient_username} successfully.", category='success')
    return redirect(url_for('views.user_files', username=current_user.userName))