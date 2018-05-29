# Define the application directory
import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# Statement for enabling the development environment
DEBUG = True
# Define the database - we are working with
# SQLite for this example
SQLALCHEMY_DATABASE_URI = 'postgres://postgres:synapsedb@localhost:5432'
DATABASE_CONNECT_OPTIONS = {}
SQLALCHEMY_TRACK_MODIFICATIONS = False
# Application threads. A common general assumption is
# using 2 per available processor cores - to handle
# incoming requests using one and performing background
# operations using the other.
THREADS_PER_PAGE = 2

# Enable protection agains *Cross-site Request Forgery (CSRF)*
CSRF_ENABLED = True

# Use a secure, unique and absolutely secret key for
# signing the data.
CSRF_SESSION_KEY = "ASDFASDFAAAa!5241@!#"

# Secret key for signing cookies
SECRET_KEY = b'_5#y2L"FFAAAz\n\xec]/'

NEUROGLANCER_URL = "http://ibs-forrestc-ux1.corp.alleninstitute.org:8002/"

