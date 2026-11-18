from app import create_app

app = create_app()

if __name__ == "__main__":
    # The Windows Store Python install can trigger Flask's file watcher from
    # changes in its own standard library, restarting the server mid-request.
    app.run(debug=False, use_reloader=False)
