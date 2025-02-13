from flask import Flask, render_template,request,url_for,redirect,jsonify,send_file

from flask_login import LoginManager,UserMixin,login_user,logout_user
from werkzeug.security import generate_password_hash, check_password_hash

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column,relationship
from sqlalchemy import Integer,String

from functools import wraps
from datetime import datetime
import re
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random

from dotenv import load_dotenv
load_dotenv()

#GLOBAL VARIABLES
is_admin = 0
current_user = None
forgot_password_email_username = None
open_otp_form = 0
show_login_form =  None
global_otp = None
choose_password = 0
wrong_otp = 0
user_content_page = None
on_general_files_upload = 0 

#1FUNCTIONS
def send_mail(receiver,body,sender = os.getenv('EMAIL')):
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(user= os.getenv('EMAIL'), password=os.getenv("EMAIL_APPPASSWORD"))
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = "SUBJECT"
    msg.attach(MIMEText(body, 'html'))
    server.sendmail(sender, receiver, msg.as_string())
    server.quit()


def send_otp(receiver):
    global global_otp
    random_otp = ''.join(random.choice(['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']) for i in range(6))
    global_otp = random_otp
    email_body = f'''<!DOCTYPE html>
                        <html>
                        <head>
                        <meta charset="UTF-8">
                        <meta http-equiv="X-UA-Compatible" content="IE=edge"> 
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>OTP Email</title>
                        </head>
                        <body style="font-family: Arial, sans-serif; background-image: linear-gradient(to bottom right, #e6f2ff, #b3d9ff); padding: 20px; margin: 0;">
                        <div style="max-width: 600px; margin: auto; background-image: linear-gradient(to bottom right, #FFD700, #FFFF00); border-radius: 10px; box-shadow: 0 0 20px rgba(0, 0, 0, 0.1); padding: 40px; text-align: center;">
                            <p style="font-size: 18px; color: #666; margin-bottom: 20px;">Dear User,</p>
                            <p style="font-size: 20px;">Your One-Time Password (OTP) is:</p>
                            <h1 style="font-size: 36px; color: #333; text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2); margin-bottom: 30px;"><span style="color: #009688; font-weight: bold;">{random_otp}</span></h1>
                            <p style="font-size: 20px; color: #444;">Please use this OTP to proceed with your action. Remember, this OTP is valid for a single use only.</p>
                            <div style="position: relative; display: inline-block; overflow: hidden; border-radius: 10px; box-shadow: 0 0 20px rgba(0, 0, 0, 0.1); margin-top: 40px;">
                                <img src="https://image.pngaaa.com/786/8630786-small.png" alt="OTP Image" style="display: block; width: 100%; transition: transform 0.5s ease-in-out;">
                            
                            </div>
                        </div>
                        </body>
                        </html>
                    '''
    send_mail(receiver = receiver, body = email_body)              
    
def remove_tags(text):
    clean_text = re.sub(r'<.*?>', '', text)
    clean_text = re.sub(r'&nbsp;|&quot;', ' ', clean_text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text

def current_time():
    current_date = datetime.now()
    day = current_date.day
    month = current_date.strftime("%B")  
    year = current_date.year
    return f"{day}/{month}/{year}"

def get_file(file_id,file_list):
    for file in file_list:
        if file.id == file_id:
            return file.name
        
application = Flask(__name__)

application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
application.config['SECRET_KEY'] = 'rahulsharmaxiershare'
application.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads') 

# application.config['SESSION_TYPE'] = 'filesystem'  # Use the filesystem for session storage
# application.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_session')  # Directory where sessions will be stored
# application.config['SESSION_PERMANENT'] = False  # Session will not be permanent
# application.config['SESSION_USE_SIGNER'] = True  # Sign the session ID cookie
# application.config['SESSION_USE_SIGNER'] = True  # Sign session cookie to avoid tamperin

# session(application)
# Ensure the upload directory exists
if not os.path.exists(application.config['UPLOAD_FOLDER']):
    os.makedirs(application.config['UPLOAD_FOLDER'])

login_manager =  LoginManager()
login_manager.init_app(application)

@login_manager.user_loader
def load_user(user_id):
    return database.session.get(User,user_id)

#GLOBAL VARIABLES
current_page = None
small_upload_button_page = None



#CLASSES
class CurrentFile:
    def __init__(self,id,name,timing,size) :
        self.id = id
        self.name = name
        self.time = timing
        self.size = size

class CurrentUser:
    def __init__(self,id,username,email,content,file):
        self.id = id
        self.username  = username
        self.email = email 
        self.content = content
        self.file = file
        
#TABLES 
class Base(DeclarativeBase):
    pass

database = SQLAlchemy(model_class = Base)
database.init_app(application)


class Content(database.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str] = mapped_column(String)
    time: Mapped[str] = mapped_column(String)
    
    # Foreign key column linking to the User table
    user_id: Mapped[int] = mapped_column(Integer, database.ForeignKey('user.id'))

    # Define a relationship between Content and User
    user = relationship('User', back_populates='contents')


class User(UserMixin, database.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String)
    created_on: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)
    password: Mapped[str] = mapped_column(String)

    # Define the relationship back to Content
    contents = relationship('Content', back_populates='user')
    
   
with application.app_context():
    database.create_all()


#RTG_FUNCTIONS
def admin_only(function):
    @wraps(function)
    def wrapper(*args,**kwargs):
        if (current_user.id != 1):
            return "<h1>only admin allowed</h1>"
        return function(*args,**kwargs)
    return wrapper    
    

@application.context_processor
def common_variable():
    global current_user
    return dict(choose_password = choose_password,
                current_user = current_user,
                wrong_password = 0,
                open_otp_form = 0,
                forgot_password_email_username =forgot_password_email_username , 
                show_login_form = show_login_form,
                wrong_otp = 0,
                on_general_files_upload = 0)

@application.route("/")
def index():
    global forgot_password_email_username,current_user,open_otp_form,show_login_form,global_otp,choose_password,wrong_otp,current_page,is_admin
    
    show_login_form = 0
    current_page = "index"
    is_admin = 0
    
    forgot_password_email_username = None
    open_otp_form = 0
    show_login_form =  None
    global_otp = None
    choose_password = 0
    wrong_otp = 0
    
    # print("--------------index route is running---------")
    # if "username" not in session:
    #     current_user = None
    return render_template("index.html")


@application.route("/upload",methods = ['POST','GET'])
def upload():
    print("--------------upload route is running---------")
    global current_user
    if request.method == "POST":
        content = request.form.get("summernote1")
        if content:    
            new_content = Content(
                content = content,
                time = current_time(),
                user_id = current_user.id if current_user else 0
            )
            
            database.session.add(new_content)
            database.session.commit()
            return render_template("index.html")

        else:
            return render_template("index.html")
    return render_template("index.html")

@application.route("/receive",methods = ['POST','GET'])
def receive():
    print("--------------receive route is running---------")
    content_object =database.session.execute(database.select(Content).where(Content.user_id == 0)).scalars().all()[-1]
    return render_template("index.html",render_content = content_object.content)



@application.route("/table_data")
def table_data():
    print("--------------table_data route is running---------")
    global current_page,small_upload_button_page,user_content_page
    current_page = "index"
    small_upload_button_page = "table_data"
    user_content_page = "table_data"
    content_data =  database.session.execute(database.select(Content).where(Content.user_id == 0)).scalars().all()
    json_data = [
        {
            'id': content.id,
            'content': remove_tags(content.content),
            'time': content.time  
        } for content in content_data
    ]
    return render_template("table_data.html", data = json_data )


@application.route("/check_for_admin")
def check_for_admin():
    print("--------------check_for_admin route is running---------")
    global is_admin ,on_general_files_upload 
    is_admin = 1
    on_general_files_upload = 1
    return redirect(url_for("table_data")) 

@application.route("/delete_content/<int:content_id>")
def delete_content(content_id):
    print("--------------delete_content route is running---------")
    global user_content_page
    content_to_delete = database.get_or_404(Content,content_id)
    database.session.delete(content_to_delete)
    database.session.commit()
    return redirect(url_for(user_content_page)) 


@application.route("/full_content/<int:content_id>",methods = ['POST','GET'])
def full_content(content_id):
    print("--------------full_content route is running---------")
    global current_page,small_upload_button_page,current_user
    small_upload_button_page = "full_content"
    current_page = "my_profile" if current_user else "table_data"
    chosen_content = database.session.execute(database.select(Content).where(Content.id == content_id)).scalar()
    return render_template("full_content.html",content_data = chosen_content)


@application.route("/back")
def back_button():
    print("--------------back_button route is running---------")
    global on_general_files_upload,current_page
    on_general_files_upload = 0
    return redirect(url_for(current_page))

@application.route('/get_json_data_content', methods=['GET'])
def get_data():
    print("--------------get_data route is running---------")
    
    contents = Content.query.all()
    data = [
        {
            'id': content.id,
            'content': content.content,
            'time': content.time  
        } for content in contents
    ]
    
    return jsonify(data)

@application.route('/get_json_data_user', methods=['GET']) #123
def get_data_user():
    print("--------------get_data_user route is running---------")
    
    users = User.query.all()
    data = [
        {
            'id': user.id,
            'username': user.username,
            'email': user.email  
        } for user in users
    ]
    
    return jsonify(data)

@application.route("/Edit/<int:content_id>",methods = ['POST','GET'])
def edit_content(content_id):
    print("--------------edit_content route is running---------")
    chosen_content = database.session.execute(database.select(Content).where(Content.id == content_id)).scalar()
    content = request.form.get("summernote2")
    chosen_content.content = content
    chosen_content.time = current_time()
    database.session.commit()
    return render_template("full_content.html",content_data = chosen_content)

@application.route("/small_upload/<int:content_id>",methods = ['POST','GET'])
def small_upload(content_id):
    global small_upload_button_page
    
    print("--------------small_upload route is running---------")
    chosen_content = database.session.execute(database.select(Content).where(Content.id == content_id)).scalar()
    
    new_content = Content( 
    content = chosen_content.content,
    time = chosen_content.time,
    user_id = 0
    )
    database.session.add(new_content)
    database.session.delete(chosen_content)
    database.session.commit()
    if small_upload_button_page == "table_data":
        content_data =database.session.execute(database.select(Content).where(Content.user_id == 0)).scalars().all()
        json_data = [
            {
                'id': content.id,
                'content': remove_tags(content.content),
                'time': content.time  
            } for content in content_data
        ]
        return render_template("table_data.html", data = json_data)
    
    return render_template("full_content.html",content_data = chosen_content)


@application.route("/user_small_upload/<int:content_id>",methods = ['POST','GET'])
def user_small_upload(content_id): #111
    global small_upload_button_page,current_user
    
    print("--------------user_small_upload route is running---------")
    chosen_content = database.session.execute(database.select(Content).where(Content.id == content_id)).scalar()
    
    new_content = Content( 
    content = chosen_content.content,
    time = chosen_content.time,
    user_id = 0
    )
    database.session.add(new_content)
    database.session.commit()
    if small_upload_button_page == "my_profile":
        print("this is here")
        content_data = database.session.execute(database.select(Content).where(Content.user_id == current_user.id)).scalars().all()
        json_data = [
            {
                'id': content.id,
                'content': remove_tags(content.content),
                'time': content.time  
            } for content in content_data
        ]
        return render_template("user_data.html", table_contents = json_data)
    
    return render_template("full_content.html",content_data = chosen_content)


@application.route('/register',methods = ['GET','POST'])
def register():
    print("--------------register route is running---------")
    global current_user
    all_user_data = database.session.execute(database.select(User)).scalars().all()
    emails = [user.email for user in all_user_data]
    usernames = [user.username for user in all_user_data]      
    if request.method =="POST":
        hashed_password = generate_password_hash(request.form.get('password'), method='pbkdf2:sha256',salt_length=8)
        new_user = User(
            username = request.form.get("username").lower(),
            created_on = current_time(),
            email = request.form.get("email").lower(),
            password = hashed_password
        )
        database.session.add(new_user)
        database.session.commit()
        login_user(new_user)
        current_user = new_user
        return render_template('index.html')
    return render_template('register.html',emails = emails,usernames = usernames)

@application.route('/login',methods = ['GET','POST'])
def login():
    print("--------------login route is running---------")
    global current_user,forgot_password_email_username,wrong_password
    username_input_data = request.form.get("username_or_email").lower()
    if request.method == "POST":
        password_input_data = request.form.get("password")
        chosen_username = None
        if("@" in username_input_data):
            chosen_username = database.session.execute(database.select(User).filter(User.email == username_input_data)).scalar()
        else:
            chosen_username = database.session.execute(database.select(User).filter(User.username == username_input_data)).scalar()
        if check_password_hash(chosen_username.password, password_input_data):
            login_user(chosen_username)
        else:
            forgot_password_email_username = username_input_data
            wrong_password = 1
            return render_template('index.html',wrong_password = 1)
        current_user = chosen_username
        return render_template('index.html')   
    return render_template('index.html')


@application.route('/my_profile')
def my_profile(): #222
    print("--------------my_profile route is running---------")
    global current_user,current_page,user_content_page,small_upload_button_page
    current_page = "index"
    user_content_page = "my_profile"
    small_upload_button_page = "my_profile"
    table_contents = database.session.execute(database.select(Content).where(Content.user_id == current_user.id)).scalars().all()
    json_data = [
        {
            'id': content.id,
            'content': remove_tags(content.content),
            'time': content.time  
        } for content in table_contents
    ]
    return render_template('user_data.html',table_contents = json_data)


@application.route('/logout')
def logout():
    print("--------------logout route is running---------")
    global current_user
    current_user = None
    logout_user()
    return redirect(url_for('index'))



@application.route('/upload_file', methods=['POST'])
def upload_file():
    print("--------------upload_file route is running---------")
    global current_user
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    
    if file:
        # Determine folder path: user-specific or general folder
        if current_user:
            user_folder = os.path.join(application.config['UPLOAD_FOLDER'], current_user.username)
        else:
            user_folder = os.path.join(application.config['UPLOAD_FOLDER'], 'general')

        # Ensure the folder exists
        os.makedirs(user_folder, exist_ok=True)  # Create folder if it doesn't exist
        
        # Save the file in the appropriate folder
        filename = os.path.join(user_folder, file.filename)
        file.save(filename)
        
        return jsonify({'message': 'File Uploaded'})
    
    return jsonify({'error': 'File upload failed'})


file_list = []
@application.route('/general_uploaded_files')
def general_uploaded_files():
    print("--------------general_uploaded_files route is running---------")
    global file_list,user_content_page
    user_content_page = "general_uploaded_files"
    
    file_list = []
    folder_path = os.path.join(application.config['UPLOAD_FOLDER'], 'general')
    if not os.path.exists(folder_path):
        return jsonify({'message': 'No files uploaded'})
    items = os.listdir(folder_path)
    file_count = 0
    for item in items:
        item_path = os.path.join(folder_path, item)
        if os.path.isfile(item_path):
            file_count += 1
            file_size = os.path.getsize(item_path)
            file_size_mb = round(file_size / (1024 * 1024), 2)
            file_list.append(CurrentFile(file_count, item, "N/A", file_size_mb))
    return render_template('uploaded_files.html', file_list=file_list , on_general_files_upload = 1 )

@application.route('/uploaded_files')
def uploaded_files():
    print("--------------uploaded_files route is running---------")
    global file_list, current_user,user_content_page
    user_content_page = "uploaded_files"
    file_list = []
    if current_user:
        folder_path = os.path.join(application.config['UPLOAD_FOLDER'], current_user.username)
    else:
        folder_path = os.path.join(application.config['UPLOAD_FOLDER'], 'general')
    if not os.path.exists(folder_path):
        return jsonify({'message': 'No files uploaded'})
    items = os.listdir(folder_path)
    file_count = 0
    for item in items:
        item_path = os.path.join(folder_path, item)
        if os.path.isfile(item_path):
            file_count += 1
            file_size = os.path.getsize(item_path)
            file_size_mb = round(file_size / (1024 * 1024), 2)
            file_list.append(CurrentFile(file_count, item, "N/A", file_size_mb))
    return render_template('uploaded_files.html', file_list=file_list)
    
    
@application.route('/download/<int:file_id>')
def download(file_id):
    print("--------------download route is running---------")
    global file_list
    file_path = f"./uploads/general/{get_file(file_id,file_list)}" 
    try:
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return str(e)    

@application.route('/user_download/<int:file_id>')
def user_download(file_id):
    print("--------------user_download route is running---------")
    global file_list, current_user
    file_path = f"./uploads/{current_user.username}/{get_file(file_id,file_list)}" 
    try:
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return str(e)    

@application.route('/delete_file/<int:file_id>')
def delete_file(file_id):
    print("--------------delete_file route is running---------")
    global current_user, file_list,user_content_page
    if current_user and user_content_page == "uploaded_files":
        folder_path = os.path.join(application.config['UPLOAD_FOLDER'], current_user.username)
    else:
        folder_path = os.path.join(application.config['UPLOAD_FOLDER'], 'general')
    file_name = get_file(file_id, file_list)
    file_path = os.path.join(folder_path, file_name)
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"File {file_name} deleted successfully.")
    else:
        print(f"File {file_name} not found.")
    
    return redirect(url_for(user_content_page))

@application.route('/change_password_inputs',methods = ['GET','POST'])
def change_password_inputs():
    print("--------------change_password_inputs route is running---------")
    global forgot_password_email_username,open_otp_form,show_login_form,global_otp,choose_password,wrong_otp
    show_login_form = 1
    open_otp_form = 1
    if(request.method == "POST"):
        entred_otp = ""
        for i in range(1,7):
            entred_otp += request.form.get(f"otp_input_{i}")
        if(entred_otp == global_otp):
            return render_template('index.html',
                                   show_login_form =show_login_form,
                                   open_otp_form = 0,
                                   choose_password = 1) 
        else:
            return render_template('index.html',
                                   show_login_form =show_login_form,
                                   open_otp_form = 1,
                                   wrong_otp = 1) 
    else:
        if("@" not in forgot_password_email_username ):
            user_email = database.session.execute(database.select(User).filter(User.username == forgot_password_email_username)).scalar()
            forgot_password_email_username = user_email.email
        send_otp(forgot_password_email_username)
        
    return render_template('index.html',
                           show_login_form =show_login_form,
                           open_otp_form = 1) 
 
@application.route('/change_password',methods = ['GET','POST'])
def change_password(): 
    print("--------------change_password route is running---------")
    global forgot_password_email_username,current_user,open_otp_form,show_login_form,global_otp,choose_password,wrong_otp
    chosen_username = None
    if (request.method == "POST"):
        new_password = request.form.get('change_password_input1')
        
        chosen_username = database.session.execute(database.select(User).filter(User.email == forgot_password_email_username)).scalar()
        print(f"THE PASS CHANGE USERNAME IS {chosen_username}")
        chosen_username.password = generate_password_hash(new_password, method='pbkdf2:sha256',salt_length=8)
        database.session.commit()
        current_user = chosen_username
        login_user(chosen_username)
    #RESET GLOBAL VARIABLES
    forgot_password_email_username = None
    open_otp_form = 0
    show_login_form =  None
    global_otp = None
    choose_password = 0
    wrong_otp = 0
    return render_template('index.html')

@application.route('/admin_access')
@admin_only 
def admin_access(): 
    print("--------------admin_access route is running---------")
    # user_data
    user_data = database.session.execute(database.select(User)).scalars().all()
    return render_template('admin_only.html',user_data = user_data)

# #END1
# import pandas as pd        
# def read_csv_to_dict_list(csv_file_path):
#      df = pd.read_csv(csv_file_path)
    
#      data_list = df.to_dict(orient='records')
    
#      return data_list
# @application.route("/insert_data")
# def insert_data():
#      # EXECUTE THIS QUERY
     
#      # -- Step 0: Drop the temp table if it already exists
#      # DROP TABLE IF EXISTS temp_ids;

#      # -- Step 1: Create a temporary table for random IDs
#      # CREATE TEMP TABLE temp_ids (new_id INTEGER UNIQUE);

#      # -- Step 2: Insert random unique 3-digit IDs into the temporary table
#      # INSERT INTO temp_ids (new_id)
#      # SELECT DISTINCT 100 + ABS(RANDOM()) % 900
#      # FROM content
#      # LIMIT (SELECT COUNT(*) FROM content);

#      # -- Step 3: Update the original table with the new random IDs
#      # WITH numbered_content AS (
#      #   SELECT id, ROW_NUMBER() OVER () AS row_num
#      #   FROM content
#      # ),
#      # numbered_ids AS (
#      #   SELECT new_id, ROW_NUMBER() OVER () AS row_num
#      #   FROM temp_ids
#      # )
#      # UPDATE content
#      # SET id = (SELECT new_id FROM numbered_ids WHERE numbered_ids.row_num = numbered_content.row_num)
#      # FROM numbered_content
#      # WHERE content.id = numbered_content.id;

#      # -- Step 4: Drop the temporary table
#      # DROP TABLE temp_ids;

#      print("--------------insert_data route is running---------")
#      all_content = database.session.execute(database.select(Content)).scalars().all()
#      data_list = read_csv_to_dict_list("output.csv")
#      count  = 0
#      print(all_content)
#      for data in data_list :
#         try:
#             all_content[count].id = data['id'] + 100
#             all_content[count].content = data['content']
#             all_content[count].time = data['time']
#             all_content[count].user_id = 0
#             database.session.commit()
#         except:
#             new_content = Content(
#                 content = data['content'],
#                 time = data['time'],
#                 user_id = 0
#             )
#             database.session.add(new_content)
#             database.session.commit()
#         print(f"------- INSERTION ITERATION {count}  -------")
#         count += 1
#      return "<h1>DATA INSERTED SUCCESSFULLY</H1>"

if __name__ == "__main__":
    application.run(debug=True)