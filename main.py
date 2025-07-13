from app import create_app  # 'app' here is the file name 'app.py'

application = create_app()  # Rename the app instance

if __name__ == '__main__':
    application.run(host='0.0.0.0', port=5000, debug=True)
