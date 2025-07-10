import click
from flask.cli import with_appcontext
from models import db, User # Import necessary models

# You might need to import your Flask app instance if db requires it,
# but usually 'with_appcontext' handles this.
# from app import create_app
# app = create_app()


@click.command('create-admin')
@click.option('--username', prompt=True, help='The username for the admin.')
@click.option('--email', prompt=True, help='The email address for the admin.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password for the admin.')
@with_appcontext # Ensures database access is available
def create_admin_command(username, email, password):
    """Creates a new admin user."""

    # Check if admin already exists
    if User.query.filter((User.email == email) | (User.username == username)).first():
        click.echo(f"Error: Admin with username '{username}' or email '{email}' already exists.")
        return

    try:
        admin = User(
            username=username,
            email=email,
            role='admin' # Set the role explicitly
            # Add other fields if they are mandatory in your model (e.g., phone_number)
            # phone_number='0000000000' # Example if needed
        )
        admin.set_password(password) # Hashes the password

        db.session.add(admin)
        db.session.commit()
        click.echo(f"Admin user '{username}' created successfully.")
    except Exception as e:
        db.session.rollback()
        click.echo(f"Error creating admin user: {str(e)}")

# Function to register commands with the app
def register_commands(app):
    app.cli.add_command(create_admin_command)

