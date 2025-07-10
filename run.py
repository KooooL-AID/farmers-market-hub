from app import create_app

# Create the app instance using the factory function
app = create_app()

# The database initialization (db.create_all()) and admin creation
# should ideally be handled by Flask-Migrate and the custom CLI command,
# so they are removed from here.

# Run the application
if __name__ == "__main__":
    # Set debug=False for production
    app.run(debug=True)
