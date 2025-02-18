from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import subprocess
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Konfiguracja bazy danych MySQL z SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://ansible_user:passwd@localhost/ansible_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicjalizacja SQLAlchemy
db = SQLAlchemy(app)

# Model Playbook
class Playbook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    playbook_path = db.Column(db.String(255), nullable=False)
    inventory_path = db.Column(db.String(255), nullable=False)

# Strona główna
@app.route('/')
def index():
    playbooks = Playbook.query.all()
    return render_template('index.html', playbooks=playbooks)

# Dodawanie nowego playbooka
@app.route('/add', methods=['POST'])
def add_playbook():
    name = request.form['name']
    playbook_path = request.form['playbook_path']
    inventory_path = request.form['inventory_path']

    new_playbook = Playbook(name=name, playbook_path=playbook_path, inventory_path=inventory_path)
    db.session.add(new_playbook)
    db.session.commit()

    flash('Playbook dodany pomyślnie!', 'success')
    return redirect(url_for('index'))

# Uruchamianie playbooka
@app.route('/run/<int:playbook_id>')
def run_playbook(playbook_id):
    playbook = Playbook.query.get_or_404(playbook_id)

    try:
        command = f"ansible-playbook -i {playbook.inventory_path} {playbook.playbook_path}"
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode()
        flash(f"Playbook uruchomiony pomyślnie:\n{output}", 'success')
    except subprocess.CalledProcessError as e:
        error_output = e.stderr.decode()
        flash(f"Błąd podczas uruchamiania playbooka:\n{error_output}", 'error')

    return redirect(url_for('index'))

# Edycja pliku YAML
@app.route('/edit/<int:playbook_id>', methods=['GET', 'POST'])
def edit_playbook(playbook_id):
    playbook = Playbook.query.get_or_404(playbook_id)

    if request.method == 'POST':
        new_content = request.form['content']
        try:
            with open(playbook.playbook_path, 'w') as file:
                file.write(new_content)
            flash('Plik YAML został zapisany pomyślnie!', 'success')
        except Exception as e:
            flash(f'Błąd podczas zapisywania pliku: {str(e)}', 'error')
        return redirect(url_for('index'))

    try:
        with open(playbook.playbook_path, 'r') as file:
            content = file.read()
    except Exception as e:
        flash(f'Błąd podczas odczytywania pliku: {str(e)}', 'error')
        return redirect(url_for('index'))

    return render_template('edit.html', playbook=playbook, content=content)

if __name__ == '__main__':
    with app.app_context():
        # Tworzenie tabel w bazie danych (jeśli nie istnieją)
        db.create_all()
    app.run(debug=True)