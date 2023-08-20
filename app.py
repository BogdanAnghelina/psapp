from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import current_user, LoginManager, UserMixin, login_user, login_required, logout_user
from database import Template, session
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

def format_variable(variable):
    # Check if the variable contains only valid characters
    if not re.match(r'^[a-zA-Z0-9_]*$', variable):
        return None
    
    # Convert to lowercase and wrap with square brackets
    return f"[{variable.lower()}]"

@login_manager.user_loader
def load_user(user_id):
    return User(user_id=user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'password':
            user = User(user_id='admin')
            login_user(user)
            return redirect(url_for('new_template'))
        else:
            flash('Invalid credentials.')
    return render_template('login.html')

@app.route('/new_template', methods=['GET', 'POST'])
@login_required
def new_template():
    template = session.query(Template).filter_by(draft=True, user_id=current_user.id).first()

    if not template:
        draft_name = "Draft #1"
        template = Template(template_name=draft_name, template_content='', draft=True, user_id=current_user.id)
        session.add(template)
        session.commit()

    if request.method == 'POST':
        if 'save_template' in request.form:
            template_name = request.form['template_name']
            template_content = request.form['template_content']
            template.template_name = template_name or "Draft #1"
            template.template_content = template_content or ''
            session.commit()
            flash('Template saved successfully!')
            return redirect(url_for('new_template'))

        elif 'add_variable' in request.form:
            variable_name = request.form['variable_name']
            formatted_variable = format_variable(variable_name)

            if not formatted_variable:
                flash('Variable can only contain letters, numbers, and underscores.')
                return redirect(url_for('new_template'))

            current_variables = template.template_variables.split(",") if template.template_variables else []
            current_variables.append(formatted_variable)
            template.template_variables = ",".join(current_variables)
            session.commit()
            flash(f'Variable {formatted_variable} added successfully!')
            return redirect(url_for('new_template'))

        elif 'delete_variable' in request.form:
            variable_to_delete = request.form['delete_variable']
            current_variables = template.template_variables.split(",") if template.template_variables else []
            if variable_to_delete in current_variables:
                current_variables.remove(variable_to_delete)
                template.template_variables = ",".join(current_variables)
                session.commit()
                flash(f'Variable {variable_to_delete} deleted successfully!')
            return redirect(url_for('new_template'))

    variables = template.template_variables.split(",") if template.template_variables else []
    return render_template('new_template.html', variables=variables)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.teardown_appcontext
def shutdown_session(exception=None):
    if exception:
        session.rollback()
    else:
        session.commit()
    session.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)