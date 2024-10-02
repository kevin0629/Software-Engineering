from flask import Flask, render_template, Response, request, redirect, url_for, flash
import subprocess
import os
import time
from datetime import datetime
import datetime
from werkzeug.utils import secure_filename
import mysql.connector

app = Flask(__name__)

if __name__ == '__main__':
    app.run(debug=True)