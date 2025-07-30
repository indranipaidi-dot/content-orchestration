
# # backend/app.py
# from flask import Flask, request, jsonify, Blueprint, current_app
# from flask_cors import CORS
# import os
# import logging
# from dotenv import load_dotenv
# from werkzeug.security import generate_password_hash, check_password_hash
# import uuid

# # --- NEW: Import JWT libraries ---
# from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager

# from google.oauth2 import id_token
# from google.auth.transport import requests as google_requests
# from google.cloud import storage
# from datetime import datetime, timedelta, timezone # Import for signed URLs

# # --- Setup ---
# load_dotenv() # This loads environment variables from .env file
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
# app = Flask(__name__)

# # --- NEW: Configuration for JWT ---
# app.config["JWT_SECRET_KEY"] = os.getenv('JWT_SECRET_KEY', "fallback-jwt-secret-key-for-dev")
# jwt = JWTManager(app)

# # --- Other Configurations ---
# app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
# app.config['GCS_BUCKET_NAME'] = os.getenv('GCS_BUCKET_NAME')

# # --- CORS Configuration ---
# # Ensures your frontend (localhost:3000) can communicate with your backend
# CORS(app, resources={r"/*": {"origins": os.getenv('REACT_APP_FRONTEND_URL', 'http://localhost:3000')}}, supports_credentials=True)


# # --- User Model and DB (In-memory for demonstration) ---
# # In a real application, you'd use a database (SQLAlchemy, MongoDB, etc.)
# class User():
#     def __init__(self, id, email, username=None, google_id=None, profile_pic_url=None, password_hash=None):
#         self.id = id
#         self.email = email
#         self.username = username or email.split('@')[0]
#         self.google_id = google_id
#         self.profile_pic_url = profile_pic_url
#         self.password_hash = password_hash
    
#     def set_password(self, password):
#         self.password_hash = generate_password_hash(password)

#     def check_password(self, password):
#         return check_password_hash(self.password_hash, password)

# _users_db = {} # Simple in-memory dictionary to simulate a user database

# # JWT user lookup callback
# @jwt.user_lookup_loader
# def user_lookup_callback(_jwt_header, jwt_data):
#     identity = jwt_data["sub"]
#     return get_user_from_db(user_id=identity)

# # Helper function to retrieve user from the in-memory DB
# def get_user_from_db(user_id=None, email=None, google_id=None):
#     if user_id: return _users_db.get(user_id)
#     for user in _users_db.values():
#         if email and user.email == email: return user
#         if google_id and user.google_id == google_id: return user
#     return None

# # Helper function to save/update user in the in-memory DB
# def save_user_to_db(user):
#     _users_db[user.id] = user
#     logger.info(f"User {user.email} saved/updated in DB.")


# # --- Google Cloud Storage Helper Functions ---

# def get_gcs_client():
#     """Initializes and returns a Google Cloud Storage client by directly using the absolute path."""
#     try:
#         # --- HARDCODED ABSOLUTE PATH ---
#         # This path was confirmed by your check_path.py script.
#         # Ensure this path is 100% correct for YOUR system.
#         credentials_path = r'C:\Users\ravee\OneDrive\Desktop\content-orchestration\content-orchestration\backend\my-credentials.json'

#         # This line checks if the file exists at the hardcoded path.
#         if not os.path.exists(credentials_path):
#             # If it still doesn't exist here, the path is wrong or there's an OS-level issue.
#             raise FileNotFoundError(f"CRITICAL ERROR: Google Cloud credentials file not found at: {credentials_path}")
        
#         logger.info(f"Using Google Cloud credentials from: {credentials_path}")
#         return storage.Client.from_service_account_json(credentials_path)
#     except Exception as e:
#         logger.error(f"FATAL: GCS client failed to initialize. Check credentials file and its path. ERROR: {e}", exc_info=True)
#         raise
    
# def create_user_gcs_folders(user_email, bucket_name):
#     """Creates initial category folders for a new user in GCS."""
#     logger.info(f"Creating GCS folders for {user_email} in {bucket_name}")
#     try:
#         storage_client = get_gcs_client()
#         bucket = storage_client.bucket(bucket_name)
#         for folder_type in ["images", "videos", "audios", "others"]:
#             # GCS doesn't have true folders, but zero-byte blobs with '/' act as placeholders
#             blob = bucket.blob(f"{user_email}/{folder_type}/")
#             if not blob.exists(): 
#                 blob.upload_from_string('', content_type='application/x-directory')
#         logger.info(f"GCS folders created/verified for {user_email}.")
#     except Exception as e:
#         logger.error(f"Failed to create GCS folders for {user_email}: {e}", exc_info=True)
#         raise

# def initialize_user_billing(user_id):
#     """Placeholder for any user-specific billing setup."""
#     logger.info(f"Placeholder: Initializing billing for user: {user_id}")


# # --- Authentication Routes Blueprint ---
# auth_bp = Blueprint('auth_bp', __name__)

# @auth_bp.route('/google_login', methods=['POST'])
# def google_login():
#     token = request.json.get('token')
#     if not token:
#         return jsonify(success=False, error="No token provided"), 400

#     try:
#         idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), current_app.config['GOOGLE_CLIENT_ID'])
#         email, name, picture = idinfo.get('email'), idinfo.get('name'), idinfo.get('picture')
#         google_user_id = idinfo['sub']

#         user = get_user_from_db(google_id=google_user_id) or get_user_from_db(email=email)

#         if not user:
#             logger.info(f"Creating new user for {email}")
#             user = User(id=google_user_id, email=email, username=name, google_id=google_user_id, profile_pic_url=picture)
#             save_user_to_db(user)
#             # This line will now call the corrected get_gcs_client()
#             create_user_gcs_folders(email, current_app.config['GCS_BUCKET_NAME'])
#             initialize_user_billing(user.id)

#         access_token = create_access_token(identity=user.id)
#         return jsonify(
#             success=True, 
#             user={'email': user.email, 'name': user.username, 'picture': user.profile_pic_url},
#             access_token=access_token
#         )
#     except Exception as e:
#         logger.error(f"Error during Google login: {e}", exc_info=True)
#         return jsonify(success=False, error='Server error during Google Login.'), 500


# # Register the authentication blueprint
# app.register_blueprint(auth_bp, url_prefix='/auth')


# # --- Protected File Upload Route ---
# @app.route('/upload_file', methods=['POST'])
# @jwt_required() # Requires a valid JWT token in the request header
# def upload_file():
#     """Handles file uploads to the user's GCS bucket."""
#     user_email_for_logging = "unknown_user"
#     print('request.files:', request.files) # <-- Good for debugging
#     print('request.form:', request.form)   # <-- Good for debugging
#     try:
#         user_id = get_jwt_identity() # Get user ID from the JWT token
#         current_user = get_user_from_db(user_id=user_id)
        
#         if not current_user:
#             return jsonify(success=False, error="User not found in database."), 404
        
#         user_email_for_logging = current_user.email

#         if 'file' not in request.files:
#             logger.warning(f"Upload attempt failed for {user_email_for_logging}: No file part in request.")
#             return jsonify(success=False, error='No file part in the request'), 400
        
#         file = request.files['file']
        
#         if file.filename == '':
#             logger.warning(f"Upload attempt failed for {user_email_for_logging}: No file selected.")
#             return jsonify(success=False, error='No selected file'), 400

#         # Determine the subfolder based on the category sent from frontend
#         category = request.form.get('category', 'others').lower()
#         subfolder_map = {
#             'images': 'images/',
#             'videos': 'videos/',
#             'audios': 'audios/'
#         }
#         subfolder = subfolder_map.get(category, 'others/')
        
#         # Construct the full path in GCS (user_email/category/filename)
#         filename = os.path.basename(file.filename) # Basic sanitization to prevent directory traversal
#         destination_blob_name = f"{current_user.email}/{subfolder}{filename}"

#         logger.info(f"Uploading '{filename}' to '{destination_blob_name}' for user {current_user.email}.")
        
#         # Upload the file to Google Cloud Storage
#         storage_client = get_gcs_client() # This will now call the corrected get_gcs_client()
#         bucket = storage_client.bucket(current_app.config['GCS_BUCKET_NAME'])
#         blob = bucket.blob(destination_blob_name)

#         blob.upload_from_file(file) # Efficiently uploads file stream

#         logger.info(f"Successfully uploaded '{filename}' for user {current_user.email}.")
#         return jsonify(success=True, message=f'File {filename} uploaded successfully.')

#     except Exception as e:
#         logger.error(f"Upload error for user {user_email_for_logging}: {str(e)}", exc_info=True)
#         return jsonify(success=False, error='An unexpected server-side error occurred during upload.'), 500
    

# # --- Protected File Search Route ---
# @app.route('/search_file', methods=['GET'])
# @jwt_required() # Requires a valid JWT token
# def search_file():
#     """Searches for a file by filename across all user's category folders in GCS."""
#     user_email_for_logging = "unknown_user"
#     try:
#         user_id = get_jwt_identity()
#         current_user = get_user_from_db(user_id=user_id)
        
#         if not current_user:
#             return jsonify(success=False, error="User not found in database."), 404
        
#         user_email_for_logging = current_user.email

#         filename_to_search = request.args.get('filename')
#         if not filename_to_search:
#             logger.warning(f"Search attempt failed for {user_email_for_logging}: No filename provided.")
#             return jsonify(success=False, error='No filename provided for search.'), 400

#         storage_client = get_gcs_client()
#         bucket = storage_client.bucket(current_app.config['GCS_BUCKET_NAME'])

#         # Define the categories to search within
#         categories_to_search = ["images", "videos", "audios", "others"]
#         found_file_url = None
#         found_file_category = None

#         # Iterate through categories to find the file
#         for category in categories_to_search:
#             # Construct the blob path for the current category
#             gcs_path = f"{current_user.email}/{category}/{filename_to_search}"
#             blob = bucket.blob(gcs_path)

#             logger.info(f"Checking for '{gcs_path}' for user {current_user.email}.")
#             if blob.exists():
#                 # If found, generate a signed URL for temporary public access (e.g., 1 hour)
#                 signed_url = blob.generate_signed_url(expiration=timedelta(hours=1), method='GET')
#                 found_file_url = signed_url
#                 found_file_category = category # Store the category where it was found
#                 logger.info(f"File '{filename_to_search}' found in category '{category}' for {current_user.email}.")
#                 break # Stop searching once the first match is found

#         if found_file_url:
#             # Return the found URL and its category for frontend rendering
#             return jsonify(success=True, file_url=found_file_url, file_category=found_file_category)
#         else:
#             logger.info(f"File '{filename_to_search}' not found in any category for user {user_email_for_logging}.")
#             return jsonify(success=False, error=f"File '{filename_to_search}' not found in your storage."), 404

#     except Exception as e:
#         logger.error(f"Search error for user {user_email_for_logging}: {str(e)}", exc_info=True)
#         return jsonify(success=False, error='An unexpected server-side error occurred during search.'), 500

# # --- Main Entry Point ---
# if __name__ == '__main__':
#     # Run the Flask app in debug mode on all available interfaces (0.0.0.0) and port 5000
#     app.run(debug=True, host='0.0.0.0', port=5000)


# backend/app.py
import os
import logging
from flask import Flask, request, jsonify, Blueprint, current_app
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

# --- JWT, Google, and Firebase/Firestore Imports ---
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google.cloud import storage
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import timedelta # Used for signed URLs expiration

# --- Setup ---
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__) # Corrected from _name_
app = Flask(__name__) # Corrected from _name_

# --- JWT Configuration ---
app.config["JWT_SECRET_KEY"] = os.getenv('JWT_SECRET_KEY', "a-default-super-secret-jwt-key-for-dev")
jwt = JWTManager(app)

# --- Other Configurations ---
app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
app.config['GCS_BUCKET_NAME'] = os.getenv('GCS_BUCKET_NAME')

# --- CORS Configuration ---
CORS(app, resources={r"/*": {"origins": os.getenv('REACT_APP_FRONTEND_URL', 'http://localhost:3000')}}, supports_credentials=True)

# --- Firebase/Firestore Initialization ---
db = None # Initialize db to None in case of failure
try:
    # Use the same absolute path for Firebase credentials as for GCS
    # This path was confirmed by your check_path.py script
    cred_path = r'C:\Users\ravee\OneDrive\Desktop\content-orchestration\backend\my-credentials.json'

    if not os.path.exists(cred_path):
        raise FileNotFoundError(f"Credentials file not found at path: {cred_path}. Please ensure it exists.")
        
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
    
    # You specified "co-user-credentials" as the database_id for firestore.client
    # If this is not a multi-database setup, you might not need database_id
    # Default behavior is usually fine unless you have multiple Firestore databases in one project.
    db = firestore.client(database_id="co-user-credentials") 
    users_collection = db.collection('co-user-credentials')
    logger.info("Successfully connected to Firestore database: co-user-credentials.")
except Exception as e:
    logger.error(f"FATAL: Could not initialize Firestore. Error: {e}", exc_info=True)
    db = None # Ensure db is None if initialization fails

# --- User Model ---
class User():
    def __init__(self, id, email, username=None, google_id=None, profile_pic_url=None, password_hash=None): # Corrected from _init_
        self.id = id
        self.email = email
        self.username = username or email.split('@')[0]
        self.google_id = google_id
        self.profile_pic_url = profile_pic_url
        self.password_hash = password_hash
    
    # Method to convert User object to a dictionary for Firestore
    def to_dict(self):
        return { 
            'id': self.id, 
            'email': self.email, 
            'username': self.username, 
            'google_id': self.google_id, 
            'profile_pic_url': self.profile_pic_url, 
            'password_hash': self.password_hash 
        }

    # Method to set password (assuming you might add local email/password login later)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Method to check password (assuming you might add local email/password login later)
    def check_password(self, password):
        # Handle case where password_hash might be None (e.g., for Google-signed users)
        if self.password_hash:
            return check_password_hash(self.password_hash, password)
        return False


# --- Firestore Helper Functions ---
def get_user_from_db(user_id=None, email=None, google_id=None):
    if not db: # Check if db was initialized successfully
        logger.error("Firestore DB not initialized. Cannot retrieve user.")
        return None
    try:
        if user_id:
            doc_ref = users_collection.document(user_id)
            doc = doc_ref.get()
            if doc.exists:
                return User(**doc.to_dict())
            return None
            
        query_ref = None
        if email:
            query_ref = users_collection.where('email', '==', email).limit(1)
        elif google_id:
            query_ref = users_collection.where('google_id', '==', google_id).limit(1)

        if query_ref:
            docs = list(query_ref.stream())
            if docs:
                return User(**docs[0].to_dict())

    except Exception as e:
        logger.error(f"Error getting user from Firestore: {e}", exc_info=True)
    return None

def save_user_to_db(user):
    if not db: # Check if db was initialized successfully
        logger.error("Firestore DB not initialized. Cannot save user.")
        return
    try:
        doc_ref = users_collection.document(user.id)
        doc_ref.set(user.to_dict())
        logger.info(f"User {user.email} saved/updated in Firestore with ID {user.id}.")
    except Exception as e:
        logger.error(f"Error saving user to Firestore: {e}", exc_info=True)

# JWT user lookup callback - NOW USES FIRESTORE
@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return get_user_from_db(user_id=identity)


# --- Google Cloud Storage Helper Functions ---
def get_gcs_client():
    """
    Initializes and returns a Google Cloud Storage client by directly using the absolute path.
    This path was confirmed by your check_path.py script.
    """
    try:
        # --- HARDCODED ABSOLUTE PATH FOR GCS CREDENTIALS ---
        # This is the path that worked in your check_path.py script.
        # Ensure this path is 100% correct for YOUR system.
        credentials_path = r'C:\Users\ravee\OneDrive\Desktop\content-orchestration\backend\my-credentials.json'

        # This line checks if the file exists at the hardcoded path.
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"CRITICAL ERROR: Google Cloud Storage credentials file not found at: {credentials_path}")
        
        logger.info(f"Using Google Cloud Storage credentials from: {credentials_path}")
        return storage.Client.from_service_account_json(credentials_path)
    except Exception as e:
        logger.error(f"FATAL: GCS client failed to initialize. ERROR: {e}", exc_info=True)
        raise

def create_user_gcs_folders(user_email, bucket_name):
    """Creates initial category folders for a new user in GCS."""
    logger.info(f"Creating GCS folders for {user_email} in {bucket_name}")
    try:
        storage_client = get_gcs_client()
        bucket = storage_client.bucket(bucket_name)
        for folder_type in ["images", "videos", "audios", "others"]:
            blob = bucket.blob(f"{user_email}/{folder_type}/")
            if not blob.exists():
                blob.upload_from_string('', content_type='application/x-directory')
        logger.info(f"GCS folders created/verified for {user_email}.")
    except Exception as e:
        logger.error(f"Failed to create GCS folders for {user_email}: {e}", exc_info=True)
        # Do not re-raise here if it's a minor issue during folder creation
        # but consider if you want this to block user login. For now, we'll log.
        
# --- Authentication Routes ---
auth_bp = Blueprint('auth_bp', __name__) # Corrected from _name_

@auth_bp.route('/google_login', methods=['POST'])
def google_login():
    if not db:
        logger.error("Attempted Google login while Firestore DB is not initialized.")
        return jsonify(success=False, error="Server database service is not available."), 503

    token = request.json.get('token')
    if not token:
        return jsonify(success=False, error="No token provided"), 400

    try:
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), current_app.config['GOOGLE_CLIENT_ID'])
        email, name, picture = idinfo.get('email'), idinfo.get('name'), idinfo.get('picture')
        google_user_id = idinfo['sub']

        user = get_user_from_db(google_id=google_user_id) # Try finding by Google ID first
        if not user:
            user = get_user_from_db(email=email) # Fallback to email if no Google ID match
            
        if not user:
            logger.info(f"Creating new user for {email} in Firestore.")
            user = User(id=google_user_id, email=email, username=name, google_id=google_user_id, profile_pic_url=picture)
            save_user_to_db(user)
            # Create GCS folders only for truly new users
            create_user_gcs_folders(email, current_app.config['GCS_BUCKET_NAME'])
            # initialize_user_billing(user.id) # Re-add if needed

        # Create an access token for the user
        access_token = create_access_token(identity=user.id)
        return jsonify(
            success=True, 
            user={'email': user.email, 'name': user.username, 'picture': user.profile_pic_url},
            access_token=access_token
        )
    except Exception as e:
        logger.error(f"Error during Google login: {e}", exc_info=True)
        # Check for specific Google Auth errors vs general exceptions
        if "Token has expired" in str(e): # Example check
             return jsonify(success=False, error='Google token expired. Please try logging in again.'), 401
        return jsonify(success=False, error='Server error during Google Login.'), 500

# Register the blueprint
app.register_blueprint(auth_bp, url_prefix='/auth')

# --- Protected File Upload Route ---
@app.route('/upload_file', methods=['POST'])
@jwt_required() # Requires a valid JWT token in the request header
def upload_file():
    """Handles file uploads to the user's GCS bucket."""
    user_email_for_logging = "unknown_user"
    print('request.files:', request.files) # For debugging
    print('request.form:', request.form)   # For debugging
    try:
        user_id = get_jwt_identity() # Get user ID from the JWT token
        current_user = get_user_from_db(user_id=user_id)
        
        if not current_user:
            return jsonify(success=False, error="User not found in database."), 404
        
        user_email_for_logging = current_user.email

        if 'file' not in request.files:
            logger.warning(f"Upload attempt failed for {user_email_for_logging}: No file part in request.")
            return jsonify(success=False, error='No file part in the request'), 400
        
        file = request.files['file']
        
        if file.filename == '':
            logger.warning(f"Upload attempt failed for {user_email_for_logging}: No file selected.")
            return jsonify(success=False, error='No selected file'), 400

        # Determine the subfolder based on the category sent from frontend
        category = request.form.get('category', 'others').lower()
        subfolder_map = {
            'images': 'images/',
            'videos': 'videos/',
            'audios': 'audios/'
        }
        subfolder = subfolder_map.get(category, 'others/')
        
        # Construct the full path in GCS (user_email/category/filename)
        filename = os.path.basename(file.filename) # Basic sanitization to prevent directory traversal
        destination_blob_name = f"{current_user.email}/{subfolder}{filename}"

        logger.info(f"Uploading '{filename}' to '{destination_blob_name}' for user {current_user.email}.")
        
        # Upload the file to Google Cloud Storage
        storage_client = get_gcs_client() # This will now call the corrected get_gcs_client()
        bucket = storage_client.bucket(current_app.config['GCS_BUCKET_NAME'])
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_file(file) # Efficiently uploads file stream

        logger.info(f"Successfully uploaded '{filename}' for user {current_user.email}.")
        return jsonify(success=True, message=f'File {filename} uploaded successfully.')

    except Exception as e:
        logger.error(f"Upload error for user {user_email_for_logging}: {str(e)}", exc_info=True)
        return jsonify(success=False, error='An unexpected server-side error occurred during upload.'), 500
    

# --- Protected File Search Route ---
@app.route('/search_file', methods=['GET'])
@jwt_required() # Requires a valid JWT token
def search_file():
    """Searches for a file by filename across all user's category folders in GCS."""
    user_email_for_logging = "unknown_user"
    try:
        user_id = get_jwt_identity()
        current_user = get_user_from_db(user_id=user_id)
        
        if not current_user:
            return jsonify(success=False, error="User not found in database."), 404
        
        user_email_for_logging = current_user.email

        filename_to_search = request.args.get('filename')
        if not filename_to_search:
            logger.warning(f"Search attempt failed for {user_email_for_logging}: No filename provided.")
            return jsonify(success=False, error='No filename provided for search.'), 400

        storage_client = get_gcs_client()
        bucket = storage_client.bucket(current_app.config['GCS_BUCKET_NAME'])

        # Define the categories to search within
        categories_to_search = ["images", "videos", "audios", "others"]
        found_file_url = None
        found_file_category = None

        # Iterate through categories to find the file
        for category in categories_to_search:
            # Construct the blob path for the current category
            gcs_path = f"{current_user.email}/{category}/{filename_to_search}"
            blob = bucket.blob(gcs_path)

            logger.info(f"Checking for '{gcs_path}' for user {current_user.email}.")
            if blob.exists():
                # If found, generate a signed URL for temporary public access (e.g., 1 hour)
                signed_url = blob.generate_signed_url(expiration=timedelta(hours=1), method='GET')
                found_file_url = signed_url
                found_file_category = category # Store the category where it was found
                logger.info(f"File '{filename_to_search}' found in category '{category}' for {current_user.email}.")
                break # Stop searching once the first match is found

        if found_file_url:
            # Return the found URL and its category for frontend rendering
            return jsonify(success=True, file_url=found_file_url, file_category=found_file_category)
        else:
            logger.info(f"File '{filename_to_search}' not found in any category for user {user_email_for_logging}.")
            return jsonify(success=False, error=f"File '{filename_to_search}' not found in your storage."), 404

    except Exception as e:
        logger.error(f"Search error for user {user_email_for_logging}: {str(e)}", exc_info=True)
        return jsonify(success=False, error='An unexpected server-side error occurred during search.'), 500

# --- Main Entry Point ---
if __name__ == '__main__':
    # Run the Flask app in debug mode on all available interfaces (0.0.0.0) and port 5000
    app.run(debug=True, host='0.0.0.0', port=5000)