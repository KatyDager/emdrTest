import pymysql
pymysql.install_as_MySQLdb()
from flask import Flask, request, jsonify, make_response, redirect, url_for
#from flask_login import login_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
import bcrypt
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity
)


from sqlalchemy.exc import IntegrityError
import requests

from flask_cors import CORS, cross_origin
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib


from sqlalchemy import create_engine, update
from sqlalchemy.orm import sessionmaker
from flask import session as login_session

from flask_mail import Mail, Message
import os

engine = create_engine(
    'mysql://root:root@127.0.0.1:3306/Emdr',
    echo=True
)
# Session = sessionmaker(bind=engine)
# session = Session()

app = Flask(__name__)

#configure flask-mail
app.config['MAIL_SERVER']='smtp.gmail.com' #smtp.googlemail.com

app.config['MAIL_PORT'] = 587 #587 for TLS, 465 for SSL
app.config['MAIL_USE_SSL'] = False #false
app.config['MAIL_USE_TLS'] = True #true

app.config['MAIL_USERNAME']='emdrtherapy234@gmail.com' #emdrtherapy234@gmail.com
app.config['MAIL_PASSWORD']='flhewlklixfqvwkq' #emdrtherapy
app.config['MAIL_DEBUG'] = True
app.config['TESTING'] = False

app.config['MAIL_SUPRESS_SEND'] = False #added but idk if it does smth

mail = Mail(app)



CORS(app)

jwt1 = JWTManager(app)

#configure db
app.config['SECRET_KEY'] = 'EMDRSecretKey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@127.0.0.1:3306/Emdr'

db = SQLAlchemy(app)

#user tabel
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(250), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(250))
    admin = db.Column(db.Boolean)
    firstname = db.Column(db.String(50))
    lastname  = db.Column(db.String(50))
    dateofbirth = db.Column(db.String(50))
    gender = db.Column(db.String(50))
    phonenumber  = db.Column(db.String(50))
    postalcode = db.Column(db.String(50))
    country = db.Column(db.String(50))

#chatbot answers tabel
class ChatBotAns(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    accord = db.Column(db.String(10))
    s2 = db.Column(db.String(50))
    s3 = db.Column(db.String(550))
    s4 = db.Column(db.String(550))
    s5 = db.Column(db.String(550))
    s6 = db.Column(db.Integer)
    s7 = db.Column(db.Integer)
    s8 = db.Column(db.String(550))
    s9 = db.Column(db.Integer)
    s10 = db.Column(db.Integer)
    s11 = db.Column(db.String(550))
    s12 = db.Column(db.String(550))
    s13 = db.Column(db.Integer)
    s14 = db.Column(db.Integer)
    s15 = db.Column(db.String(1000))
    user_public_id = db.Column(db.String(255))
  
db.create_all() 
   
#function for admin
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
            print(token)

        if not token:
            return jsonify({'message' : 'Token is missing!'}), 401

        try: 
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms="HS256")
            current_user = User.query.filter_by(public_id=data['public_id']).first()
        except:
            return jsonify({'message' : 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

#admin route to see all users
@app.route('/user', methods=['GET'])
@token_required
def get_all_users(current_user):

    if not current_user.admin:
        return jsonify({'message' : 'Cannot perform that function!'})

    users = User.query.all()

    output = []

    for user in users:
        user_data = {}
        user_data['public_id'] = user.public_id
        user_data['email'] = user.email
        user_data['password'] = user.password
        user_data['admin'] = user.admin
        output.append(user_data)

    return jsonify({'users' : output})

#admin route to see one user based on its public id
@app.route('/user/<public_id>', methods=['GET'])
@token_required
def get_one_user(current_user, public_id):

    if not current_user.admin:
        return jsonify({'message' : 'Cannot perform that function!'})

    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'message' : 'No user found!'})

    user_data = {}
    user_data['public_id'] = user.public_id
    user_data['email'] = user.email
    user_data['password'] = user.password
    user_data['admin'] = user.admin

    return jsonify({'user' : user_data})

#admin route to create a new user-TBC for all fields neecessary
@app.route('/user', methods=['POST'])
@token_required
def create_user(current_user):
    if not current_user.admin:
        return jsonify({'message' : 'Cannot perform that function!'})

    data = request.get_json()

    hashed_password = generate_password_hash(data['password'], method='sha256')

    new_user = User(public_id=str(uuid.uuid4()), email=data['email'], password=hashed_password, admin=False)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message' : 'New user created!'})

#admin route to promote a user based on its public id, make it admin from regular
@app.route('/user/<public_id>', methods=['PUT'])
@token_required
def promote_user(current_user, public_id):
    if not current_user.admin:
        return jsonify({'message' : 'Cannot perform that function!'})


    user = User.query.filter_by(public_id=public_id).first()


    if not user:
        return jsonify({'message' : 'No user found!'})

    user.admin = True
    db.session.commit()

    return jsonify({'message' : 'The user has been promoted!'})

#admin route delete a user based on its public id
@app.route('/user/<public_id>', methods=['DELETE'])
@token_required
def delete_user(current_user, public_id):
    if not current_user.admin:
        return jsonify({'message' : 'Cannot perform that function!'})

    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'message' : 'No user found!'})

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message' : 'The user has been deleted!'})

#log in route
@app.route('/login', methods=['POST'])
def login():
    #basic authorization header
    auth = request.authorization
    
    #if it does not have an authorization header, or email inputed, or password inputed
    if not auth or not auth.username or not auth.password:        
        return make_response('Could not verify email or password', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

    #search for user by email
    user = User.query.filter_by(email=auth.username).first()

    #if user does not exist
    if not user:
        return make_response('User does not exist', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})
    
    #check if the password inputed is the same as the password from db 
    if check_password_hash(user.password, auth.password):
        token = jwt.encode({'public_id' : user.public_id, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=120)}, app.config['SECRET_KEY'],algorithm="HS256")

    new_token=str(token)
        return jsonify({'token' : new_token[2:-1]}, 200)
    
    print(user.password)
    print(auth.password)
    print(user)
    return make_response('Username or password is incorrect', 403, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

#registration route
@app.route('/register', methods=['POST'])
def register():
    try:
        #get jsons with data inputed by the user
        email = request.json.get('email')
        password = request.json.get('password')
        #hashed = generate_password_hash(request.json.get('password'), method='sha256')
        repeat_password = request.json['repeat_password']
        firstname = request.json['firstname']
        lastname  = request.json['lastname']
        dateofbirth = request.json['dateofbirth']
        gender = request.json['gender']
        phonenumber  = request.json['phonenumber']
        postalcode = request.json['postalcode']
        country = request.json['country']
        
        #check if the passwords match
        
        
        # if (repeat_password != hashed):
        #     return jsonify({'errorENG' : 'Passwords do not match!', 'errorRO' : 'Parolele nu sunt identice!'}), 400
        
        
        if (repeat_password != password):
            return jsonify({'errorENG' : 'Passwords do not match!', 'errorRO' : 'Parolele nu sunt identice!'}), 400
        
        #check if the user wrote data in all inputs
        if not email:
            return jsonify({'errorENG' : 'No email provided!'}, {'errorRO' : 'Niciun email introdus!'}), 400
        if not password:
            return jsonify({'errorENG' : 'No password provided!'}, {'errorRO' : 'Nicio parola introdusa!'}), 400
        if not repeat_password:
            return jsonify({'errorENG' : 'No repeat password provided!'}, {'errorRO' : 'Nicio repetare a parolei introdusa!'}), 400
        if not firstname:
            return jsonify({'errorENG' : 'No firstname provided!'}, {'errorRO' : 'Niciun prenume introdus!'}), 400
        if not lastname:
            return jsonify({'errorENG' : 'No lastname provided!'}, {'errorRO' : 'Niciun nume introdus'}), 400
        if not dateofbirth:
            return jsonify({'errorENG' : 'No dateofbirth provided!'},  {'errorRO' : 'Nicio zi de nastere introdusa!'}), 400
        if not gender:
            return jsonify({'errorENG' : 'No gender provided!'},  {'errorRO' : 'Niciun gen introdus!'}), 400
        if not phonenumber :
            return jsonify({'errorENG' : 'No phonenumber provided!'}, {'errorRO' : 'Niciun numar de telefon introdus!'}), 400
        if not postalcode:
            return jsonify({'errorENG' : 'No postalcode provided!'}, {'errorRO' : 'Niciun cod postal introdus!'}), 400
        if not country:
            return jsonify({'errorENG' : 'No country provided!'}, {'errorRO' : 'Nicio tara introdusa!'}), 400

        
        hashed = generate_password_hash(password, method='sha256')
        
       #find if the email is already registered in the db, if it is=>error
        user = User.query.filter_by(email=email).first()
        # if bool(User.query.filter_by(email=email).first())==True:
        #     return jsonify ({'errorENG' :'Email address already exists.'}, {'errorRO' :'Adresa de e-mail este folosita.'})
            
    
        if user:
            return jsonify ({'errorENG' :'Email address already exists.'}, {'errorRO' :'Adresa de e-mail este folosita.'}), 400
        
        #create token with all the data inputed by the user
        token = jwt.encode({'email' : email, 'password' : hashed, 'firstname':firstname, 'lastname':lastname, 'dateofbirth':dateofbirth, 'gender':gender, 'phonenumber':phonenumber, 'postalcode':postalcode, 'country':country,'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'],algorithm="HS256")


#create mail using flask-mail
        msg = Message()
        msg.subject = "Account activation"
        msg.recipients = [email]
        msg.sender = app.config.get("MAIL_USERNAME")
        message="https://emdr-therapy.netlify.app/accountActivated/"
        new_token=str(token)
        message2=message+new_token[2:-1]
        message3="To activate your account, visit the following link:"+"\n"+message2+"\n"+"The link will expire in 30 minutes. "
        msg.body=message3  
        
        
    #     msg.body = f'''To activate your account, visit the following link:
    # # {url_for('activateAccount', token=token, _external=True)}
    # # The link will expire in 30 minutes. 
    # # '''
    
        mail.send(msg)
        return jsonify({'message' : 'Mail sent!'})
    
#create mail without flask-mail
    #     msgReset = f'''To activate your account, visit the following link:
    # {url_for('activateAccount', token=token, _external=True)}
    # The link will expire in 30 minutes. 
    # '''
    
    #     sender_email = "emdrtherapy234@gmail.com"
    #     receiver_email = email
    #     sender_pass = "emdrtherapy"
        
    #     msg = MIMEText(msgReset)
        
    #     msg['Subject'] = "Account activation" 
    #     msg['From'] = 'emdrtherapy234@gmail.com'
    #     msg['To'] = email
    
        
        
    #     server = smtplib.SMTP('smtp.gmail.com', 587)
    #     server.starttls()
    
    #     try:
    #         server.login(sender_email, sender_pass)
    #         print("Login success")
    #         server.sendmail(sender_email, receiver_email, msg.as_string())
    #         print("Email has been sent to ", receiver_email)  
    #         response = jsonify({'message':"The e-mail has been sent"})
    
    
    #         return response
    
    #     except Exception as e:
    #         print(e)
    #         response = jsonify({'error':'Something went wrong'})
    #         return response, 400
      
     #   return "Mail sent"
                  
        
    # except IntegrityError:
    #     # the rollback func reverts the changes made to the db ( so if an error happens after we commited changes they will be reverted )
    #     db.session.rollback()
      #  return jsonify({'errorENG' :'User Already Exists'}, {'errorRO' : 'Un user cu acest email deja exista!'}), 400
    except AttributeError:
        return jsonify({'message' :'Provide an Email and Password in JSON format in the request body'}), 400

#route for account activation
@app.route('/ActivateAccount/<token>', methods=['POST'])
def activateAccount(token):
    try:
        #decode the token from the activation link
        decoded=jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        #get all the inputs from the token
        public_id=str(uuid.uuid4())
        email=decoded.get("email")  
        hashed=decoded.get("password") 
        firstname=decoded.get("firstname") 
        lastname=decoded.get("lastname") 
        dateofbirth=decoded.get("dateofbirth") 
        gender=decoded.get("gender") 
        phonenumber=decoded.get("phonenumber") 
        postalcode=decoded.get("postalcode") 
        country=decoded.get("country") 
        admin=False

        print(decoded)
        
        #insert new user in db
        user = User(public_id=public_id, email=email, password=hashed, firstname=firstname, lastname=lastname, admin=admin, dateofbirth=dateofbirth, gender=gender, phonenumber=phonenumber, postalcode=postalcode, country=country)
        db.session.add(user)
        db.session.commit()
    

        return jsonify({'message' : 'Your account has been activated!'})
    #if the link expired or any other problem
    except jwt.ExpiredSignatureError as error:
        print (error)
        return jsonify({'message' : "The link has expired"}), 400


#route for the questions of the chatbot in Romanian 
@app.route('/chatbotRO', methods=['GET', 'POST'])  
def chatRO():
    #Intrebari chatbot
    nume_chatbot = "Cum te nume??ti?"
    varsta_chatbot = "Ce v??rst?? ai?"
    gen_chatbot = "Care este genul t??u? R??spunde cu M pentru b??rbat sau F pentru femeie."
    acord_chatbot = "Am nevoie de acordul t??u pentru p??strarea datelor oferite, pentru a-??i putea oferi interven??ia EMDR. R??spunde cu DA dac?? e??ti de acord."
     
    s2_gaseste_amintirea_negativa_chatbot = "Identific?? o emo??ie negativ?? care te cople??e??te adeseori, cu care te confrun??i frecvent ??i cu care dore??ti s?? lucrezi ast??zi? Poate fi vorba de team??, furie, spaim??, ru??ine, ne??ncredere, disperare, triste??e etc, sau poate avea forma unei senza??ii, a unei imagini care apare pe ecranul min??ii tale sau orice alt?? form?? care nu are un nume cunoscut, dar o sim??i, este acolo. Ia-??i c??teva momente ??i g??nde??tete la acea emo??ie cople??itoare cu care ai vrea s?? lucrezi ast??zi. Ia-??i un moment ??i stai cu aceast?? emo??ie. R??spunde cu DA, dup?? ce ai reu??it sa te idenifici cu acea emo??ie."
    s3_amintire_negativa_chatbot = "Pornind de la emo??ia pe care ai accesat-o, f?? o c??l??torie ??n memoria ta, p??n?? ??n cele mai vechi timpuri din care p??strezi amintiri ??i caut?? primul moment din via??a ta c??nd te-ai sim??it a??a. Alege amintirea care ????i apare prima oar?? ??n g??nd. ??ncearc?? s??-??i aminte??ti evenimentul a??a cum s-a ??nt??mplat atunci. Este un eveniment care a influen??at felul t??u de a tr??i emo??iile p??n?? ??n ziua de azi. Ia-??i timpul de care ai nevoie ??i vizualizeaz?? acel moment. Creeaz?? ??n minte o secven????, ca un cadru de film ??n care s?? pui aceast?? amintire. ??n momentul ??n care ai reu??it s?? identifici acel moment, descrie-l pe scurt."
    s4_senzatii_corporale_chatbot = "Acum c??nd te g??nde??ti la acel eveniment, la scena pe care ai identificat-o concentreaz??-??i aten??ia asupra corpului t??u, asupra senza??iilor pe care le sim??i ??n corp atunci c??nd te g??nde??ti la evenimentul respectiv. Pot fi tensiuni, poate fi ap??sare, poate fi c??ldur?? sau frig, poate fi orice alt?? senza??ie a??a cum apare ea ??n corpul t??u. ??ncearc?? totodat?? s?? vezi dac?? sunt sunete care apar ??n con??tiin??a ta atunci c??nd te g??nde??ti la acel moment. Ia-??i timpul de care ai nevoie pentru a accesa senza??iile, sunetele, mirosurile pe care ??i le evoc?? amintirea respectiv??. ??n momentul ??n care ai reu??it s?? le accesezi, noteaz??-le aici."
    s5_credinta_negativa_chatbot = "Emo??iile noastre au adeseori ??n spatele lor g??nduri, credin??e pe care ni le-am dezvoltat pe baza experien??elor noastre de via????. Ia-??i c??teva momente ??i ??ncearc?? s?? identifici ce g??nd sau credin???? negativ?? despre tine sau via???? ai dezvoltat pornind de la acel moment evocat mai devreme. Poate fi o formul?? precum:  ???sunt o victim?????, ???nu o s?? mai fiu niciodat?? normal???, ???nu sunt bun de nimic???, ???nu cred c?? voi trece peste asta???, ???oamenii ??ntotdeauna pleac??/ ??n??al?? etc???. Ia-??i timpul de care ai nevoie ??i identific?? g??ndul, credin??a cu care ai r??mas ??n urma acelui eveniment, pe care ??i-o spui adeseori ??n g??nd. ??n momentul ??n care ai reu??it s?? accesezi acea credin???? negativ??, adaug?? aici"
    s6_str_credinta_negativa_chatbot = "??n momentele care urmeaz?? o s?? te rog s?? te g??nde??ti la acest g??nd/ credin???? negativ?? ??i s?? dai o not??, c??t de adev??rate sim??i acum, ??n acest moment,  aceste cuvinte, identificate mai devreme. pe o scar?? de la 1 la 7, unde 1 este complet fals ??i 7 ??? total adev??rat:"
    s7_str_emotie_negativa_chatbot = "De asemenea, am s?? te rog s?? acorzi o not?? ??i emo??iilor pe care le sim??i cu privire la acest eveniment. Pe o scal?? de la 0 la 10, unde 0 - nu este tulbur??tor sau neutru ??i 10 este cea mai tulbur??toare posibil?? imagine pe care ??i-o po??i imagina, c??t de tulbur??toare se simte acum?"
    s8_tratament_EMDR_chatbot = "??n urm??toarele minute va urma o prim?? sesiune de tratament. Te rog s?? ????i concentrezi aten??ia asupra bilei de pe ecran ??i s?? o urm??re??ti cu privirea. ??n timp ce te vei concentra pe mi??carea de pe ecran, g??nde??te-te la evenimentul identificat mai devreme ??i d??-??i voie s??-l retr??ie??ti. Adu ??n sfera con??tiin??ei tale toate imaginile ??i sunetele, senza??iile corporale ??i credin??a negativ?? pe care le-ai identificat mai devreme. Aminte??te-??i c?? e important ca ??n timp ce retr??ie??ti incidentul, s?? urm??re??ti cu privirea mi??carea de pe ecran."
    s9_str_credinta_nevativa_dupa_emdr = "Te rog s?? s?? evaluezi din nou, g??ndurile tale cu privire la incident, c??t de adev??rate sim??i acum aceste cuvinte (g??ndurile, credin??a negativ?? identificat?? anterior) pe o scar?? de la 1 la 7, unde 1 este complet fals ??i 7 ??? total adev??rat:"
    s10_str_emotie_negativa_dupa_emdr_chatbot = "Te rog s?? evaluezi din nou emo??iile pe care le sim??i g??ndindu-te  la incident, pe o scal?? de la 0 la 10, unde 0 - nu este tulbur??tor sau neutru ??i 10 este cea mai tulbur??toare posibil?? imagine pe care ??i-o po??i imagina, c??t de tulbur??toare se simte acum?"
    s11_credinta_pozitiva_chatbot = "G??ndurile, credin??ele noastre sunt adeseori ira??ionale. Din faptul c?? cineva ne-a ??n??elat ??ncrederea la un moment dat, dezvolt??m credin??a c?? to??i oamenii ??n??al??. Din faptul c?? via??a ne-a fost pus?? ??n pericol la un moment dat, tragem concluzia c?? primejdia ne p??nde??te la orice pas. ??i totu??i exist?? oameni care nu ??n??al??, exist?? locuri ??i momente ??n care suntem ??n siguran????. Ia-??i un moment, folose??te-??i imagina??ia ??i creativitatea  ??i caut?? un nou g??nd, o nou?? credin???? pozitiv??, s??n??toas?? care s?? ??nlocuiasc?? g??ndul/ credin??a negativ?? identificat?? mai devreme. Ia-??i timpul de care ai nevoie ??i caut?? o credin???? s??n??toas?? pe care s?? o a??ezi ??n con??tiin??a ta ??n locul credin??ei negative cu care ai tr??it de la acel eveniment. ??n momentul ??n care ai identificat-o, te rog s?? o adaugi aici"
    s12_tratament_emdr_chatbot = "??n urm??toarele minute va urma o nou?? sesiune de tratament. ??n timp ce te vei concentra pe mi??carea de pe ecran, ??ncearc?? s?? retr??ie??ti evenimentul amintit mai devreme, imaginile ??i sunetele asociate, senza??iile corporale ??i credin??a pozitiv?? identificat??. Aminte??te-??i c?? e important ca ??n timp ce retr??ie??ti incidentul, s?? urm??re??ti cu privirea mi??carea de pe ecran."
    s13_str_credinta_pozitiva_dupa_emdr_chatbot = "Te rog s?? s?? evaluezi din nou, g??ndurile tale cu privire la incident, c??t de adev??rate sim??i acum aceste cuvinte (g??ndurile, credin??a pozitiv?? identificat?? anterior) pe o scar?? de la 1 la 7, unde 1 este complet fals ??i 7 ??? total adev??rat:"
    s14_str_emotie_negativa_dupa_emdr_chatbot = "Te rog s?? evaluezi din nou emo??iile pe care le sim??i g??ndindu-te  la incident, pe o scal?? de la 0 la 10, unde 0 - nu este tulbur??tor sau neutru ??i 10 este cea mai tulbur??toare posibil?? imagine pe care ??i-o po??i imagina, c??t de tulbur??toare se simte acum?"
    s15_feedbackRO_chatbot = "Las??-ne o impresie/sugestie despre interven??ia de azi:"
    
    #lista intrebari chatbot
    intrebari_ro=[nume_chatbot, varsta_chatbot, gen_chatbot, acord_chatbot, s2_gaseste_amintirea_negativa_chatbot, s3_amintire_negativa_chatbot, s4_senzatii_corporale_chatbot, s5_credinta_negativa_chatbot, s6_str_credinta_negativa_chatbot, s7_str_emotie_negativa_chatbot, s8_tratament_EMDR_chatbot, s9_str_credinta_nevativa_dupa_emdr, s10_str_emotie_negativa_dupa_emdr_chatbot, s11_credinta_pozitiva_chatbot, s12_tratament_emdr_chatbot, s13_str_credinta_pozitiva_dupa_emdr_chatbot, s14_str_emotie_negativa_dupa_emdr_chatbot, s15_feedbackRO_chatbot]
    
    #intrebarile sunt serializate in format json si trimise
    return jsonify({'intrebari_ro':intrebari_ro}) , 200  


#route for the questions of the chatbot in English
@app.route('/chatbotENG', methods=['GET', 'POST'])  
def chatENG(): 
    #Intrebari chatbot
    name_chatbot = "What???s your name?"
    age_chatbot = "How old are you?" 
    gender_chatbot = "What is your gender? Answer with M for Male or F for Female."
    accord_chatbot = "We need your permission to keep your answers stored in order to improve your EMDR intervention. Answer 'Yes' if you wish to give your permission."

    s2_find_negative_emotion_chatbot = "Please, identify a negative emotion that often overwhelms you, that you face frequently, and that you want to work with today. It can be fear, anger, fear, shame, distrust, despair, sadness etc., or it can be in the form of a sensation, an image that appears on the screen of your mind or any other form that does not have a known name, but you feel it, it is there. Take a few moments and think about that overwhelming emotion you would like to work with today. Take a moment and stay with this emotion. Answer YES, after you have managed to identify that emotion."
    s3_negative_emotion_chatbot = "Starting from the emotion you accessed, take a journey in your mind, back to the earliest times from which you keep memories and pinpoint the first moment in your life when you felt that way. Choose the memory that first comes to mind. Try to remember the event as it happened then. It is an event that has influenced your way of living emotions to this day. Take the time you need and visualize that moment. Create a sequence in your mind, like a movie frame in which you can visualize the memory. When you have managed to identify that moment, describe it briefly. "
    s4_body_sensation_chatbot = "Now that you are thinking about that event, focus on the scene you identified, focus on your body, on the sensations you feel in your body when you think about that event. There may be tensions, there may be pressure, it can be warm or cold, it can be any other sensation. Also try to see if there are sounds that appear in your consciousness when you think about that moment. Take the time you need to access the sensations, sounds, smells that your memory evokes. When you have managed to access them, write them down here."
    s5_negative_thought_chatbot = "Our emotions often have thoughts behind them, beliefs that we have developed based on our life experiences so far. Take a few moments and try to identify what negative thought or belief about you or life itself you have developed starting from that moment evoked earlier. It can be a formula like: 'I am a victim', 'I will never be normal again', 'I am not good at anything', 'I do not think I will get over it', 'people always leave/cheat, etc.' Take the time you need and identify the thought, the thought you were left with after that event, which stuck in your mind. The moment you managed to access that negative belief, add it here"
    s6_grade_negative_thought_chatbot = "In the following moments I will ask you to think about this negative thought / belief and grade, on a scale of 1 to 7 based on how real these thoughts/beliefs seem to you right now , where 1 is completely false and 7 - totally real:"
    s7_grade_negative_emotion_chatbot = "I will also ask you to give a note to the emotions you feel about this event. On a scale of 0 to 10, where 0 - is not disturbing/I feel neutral and 10 ??? it is the most disturbing image you can possibly imagine, how disturbing does it feel now?"
    s8_EMDR_treatment_chatbot = "In the next few minutes you will attend the therapy session. Please focus your attention on the ball on the screen and follow it as it moves. As you focus on the movement on the screen, think about the event identified earlier and allow yourself to relive it. Bring into the sphere of your consciousness all the images and sounds, bodily sensations, and negative thoughts/beliefs that you identified earlier. Remember that it is important to watch the movement on the screen while reliving the incident. Please write Ok when you are ready to start."
    s9_grade_negative_faith_after_emdr_chatbot = " Please re-evaluate your thoughts on the incident, how true you feel these words (thoughts, negative thoughts previously identified) on a scale of 1 to 7, where 1 is completely false and 7 - totally real:"
    s10_grade_negative_emotion_after_emdr_chatbot = " Please re-evaluate the emotions you feel thinking about the incident, on a scale from 0 to 10, where 0 - is not disturbing/I feel neutral and 10 ??? it is the most disturbing image you can possibly imagine. How disturbing does it feel now?"
    s11_positive_thought_chatbot = "Our thoughts and beliefs are often irrational. If someone deceived our trust at one point, we develop a feeling of mistrust and tend to believe all people are deceiving. If our lives were endangered at some point, we conclude that danger lurks at every step. And yet there are people who do not deceive or cheat and there are places in which we are safe. Take a moment, use your imagination and look for a new thought, a new positive, healthy belief to replace the negative thought / belief identified earlier. Take the time you need and look for a healthy belief to put in your conscience instead of the negative one you lived with since the event. Once you have identified it, please add it here"
    s12_emdr_treatment_chatbot = " A new treatment session will follow in the next few minutes. As you focus on the movement on the screen, try to relive the event mentioned earlier, the associated images and sounds, bodily sensations, and the identified positive faith. Remember that it is important to watch the movement on the screen while reliving the incident. Please write Ok when you are ready to start."
    s13_grade_positive_thought_after_emdr_chatbot = "Please re-evaluate your thoughts on the incident, how intense you feel these thoughts, positive beliefs previously identified on a scale of 1 to 7, where 1 is completely false and 7 ??? very intense:"
    s14_grade_negative_emotion_after_emdr_chatbot = " Please re-evaluate the emotions you feel thinking about the traumatic incident, on a scale of 0 to 10, where 0 - is not disturbing/ I feel neutral and 10 ??? it is the most disturbing image you can possibly imagine. How disturbing is it now? "
    s15_feedbackENG_chatbot = "Give us an impression / suggestion about today's intervention:"
    
    #lista intrebari chatbot
    intrebari_eng=[name_chatbot, age_chatbot, gender_chatbot, accord_chatbot, s2_find_negative_emotion_chatbot, s3_negative_emotion_chatbot, s4_body_sensation_chatbot, s5_negative_thought_chatbot, s6_grade_negative_thought_chatbot, s7_grade_negative_emotion_chatbot, s8_EMDR_treatment_chatbot, s9_grade_negative_faith_after_emdr_chatbot, s10_grade_negative_emotion_after_emdr_chatbot, s11_positive_thought_chatbot, s12_emdr_treatment_chatbot, s13_grade_positive_thought_after_emdr_chatbot, s14_grade_negative_emotion_after_emdr_chatbot, s15_feedbackENG_chatbot]
    
    #intrebarile sunt serializate in format json si trimise
    return jsonify({'intrebari_eng':intrebari_eng}) , 200 


#route for chatbot answers
@app.route("/chatbotAns", methods=["GET","POST"])
def chatAns():
        
    if request.is_json:
        # JSON=>Python dictionary
        dictQ = request.get_json()
        
        #AuthorizationB header for Bearer token where the public id is encoded        
        auth_h=request.headers.get('AuthorizationB')
        
        if not auth_h:
            return jsonify({'message' :'No authorization header'}), 401
        
        access_token = auth_h.split(" ")[-1]
        print(access_token)
        print("--------")
        
        #if the authorization header and the token exist, the token will be decoded, if not=>error
        if auth_h and access_token:
            public_id = jwt.decode(access_token,app.config['SECRET_KEY'],algorithms="HS256")
            public=public_id.get("public_id")
            print(public)
        else:
            return jsonify({'message' :'No authorization'}), 401
        
        #populate the dictionary with the answers and the public id of the user
        dictDB=ChatBotAns(**dictQ, user_public_id=public)
        db.session.add(dictDB)
        db.session.commit()
        
        # Print the dictionary
        print(dictQ)

        return "JSON received!", 200
    
    else:

        return "Request was not JSON", 400


#route for send mail
@app.route("/sendemail", methods=["POST"])
def sendmail():
    
    email=request.json.get('email')
    name=request.json.get('name')
    phone=request.json.get('phone')
    messageContact=request.json.get('message')
    
    if not email:
        return jsonify({'errorENG' : 'No email provided!'}, {'errorRO' : 'Niciun email introdus!'}), 400
    if not name:
        return jsonify({'errorENG' : 'No name provided!'}, {'errorRO' : 'Niciun nume introdus!'}), 400
    if not phone:
        return jsonify({'errorENG' : 'No phone provided!'}, {'errorRO' : 'Niciun numar de telefon introdus!'}), 400
    if not messageContact:
        return jsonify({'errorENG' : 'No message provided!'}, {'errorRO' : 'Niciun mesaj introdus!'}), 400
       
    # print(email)
    # print("-------------------")
    # print(subject)
    # print("-------------------")
    # print(messageContact)
    # print("-------------------")
    
    if not (email and messageContact):
        return jsonify({'errorENG':'Please fill in all fields'}, {'errorRO':'Va rugam sa completati toate campurile'})
    
    msg = Message()
    msg.subject = "From " + email + " Name: " + name + " Phone: " + phone
#    print(msg.subject)
#    print("-------------------")
    msg.recipients = app.config.get("MAIL_USERNAME").split()
#    print(msg.recipients)
#    print("-------------------")
    msg.sender = app.config.get("MAIL_USERNAME")
#    print(msg.sender)
#    print("-------------------")
    msg.body=messageContact
#    print(msg.body)

    mail.send(msg)
    

    
    return jsonify({'message' :"Mail sent"})
    
    # if not(request.json.get('username') and request.json.get('phonenumber') and request.json.get('email') and request.json.get('message')):
    #         # return Response("{error:'Please fill in all fields'}", status = 400 , mimetype='application/json')
    #         response = jsonify({'error':'Please fill in all fields'})
    #         return response, 400
            
        
    # username = request.json['username']
    # phonenumber = request.json['phonenumber']
    # email = request.json['email']
    # message = request.json['message']
    
    # sender_email = "emdrtherapy234@gmail.com"
    # receiver_email = "emdrtherapy234@gmail.com"
    # sender_pass = "emdrtherapy"
    
    # msg = MIMEText(message)
    
    # msg['Subject'] = "EMDR username:" + username + "   Phone Number:" + phonenumber + "   Email address:" + email
    # msg['From'] = 'emdrtherapy234@gmail.com'
    # msg['To'] = 'emdrtherapy234@gmail.com'

    
    
    # server = smtplib.SMTP('smtp.gmail.com', 587)
    # server.starttls()
    # try:
    #     server.login(sender_email, sender_pass)
    #     print("Login success")
    #     server.sendmail(sender_email, receiver_email, msg.as_string())
    #     print("Email has been sent to ", receiver_email)  
    #     response = jsonify({'message':"mail sent"})


    #     return response
    
    # except Exception as e:
    #     print(e)
    #     response = jsonify({'error':'Something went wrong'})
    #     return response, 400


#route for forgot password
@app.route("/ForgotPassword", methods=['POST'])
def send_reset_email():
    #get the email from json
    email=request.json.get('email')
    
    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify ({'errorENG' :'Email address does not exist.'}, {'errorRO' :'Adresa de e-mail nu exista.'})
        
    
    token = jwt.encode({'email' : email, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'],algorithm="HS256")
    message= "https://emdr-therapy.netlify.app/resetPassword/"
    message2=message+token
    message3="To reset your password, visit the following link:"+ "\n " +message2+ "\n"+"The link will expire in 30 minutes."+"\n"+"If you did not make this request then simply ignore this email and no changes will be made."
    msg = Message()
    msg.subject = "Reset Password"
    msg.recipients = [email]
    msg.sender = app.config.get("MAIL_USERNAME")
#    msg.body = f'''To reset your password, visit the following link:
#  #{url_for('reset_token', token=token, _external=True)}
#  #The link will expire in 30 minutes.
#  #If you did not make this request then simply ignore this email and no changes will be made. 
#  #'''
    msg.body=message3

    mail.send(msg)
    
#     msgReset = f'''To reset your password, visit the following link:
# {url_for('reset_token', token=token, _external=True)}
# The link will expire in 30 minutes.
# If you did not make this request then simply ignore this email and no changes will be made. 
# '''

#     sender_email = "emdrtherapy234@gmail.com"
#     receiver_email = email
#     sender_pass = "emdrtherapy"
    
#     msg = MIMEText(msgReset)
    
#     msg['Subject'] = "Password Reset Request" 
#     msg['From'] = 'emdrtherapy234@gmail.com'
#     msg['To'] = email

    
    
    # server = smtplib.SMTP('smtp.gmail.com', 587)
    # server.starttls()
    
    # try:
    #     server.login(sender_email, sender_pass)
    #     print("Login success")
    #     server.sendmail(sender_email, receiver_email, msg.as_string())
    #     print("Email has been sent to ", receiver_email)  
    #     response = jsonify({'message':"The e-mail has been sent"})


    #     return response
    
    # except Exception as e:
    #     print(e)
    #     response = jsonify({'error':'Something went wrong'})
    #     return response, 400
  
    return jsonify({'message' :"Mail sent"})

#https://emdr-therapy.netlify.app/resetPassword/    
@app.route("/resetPassword/<token>", methods=['PUT'])
def reset_token(token):    
    try:
        decoded=jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        emailU=decoded.get("email")  

#e bine sa pun parola deja hashed hashed= generate pass hashed(request.json.get pass)
        #hashed = generate_password_hash(request.json.get('password'), method='sha256')
        password = request.json.get('password')
        hashed = generate_password_hash(password, method='sha256')
        
        user = User.query.filter_by(email=emailU).first()
        user.password=hashed
    
        db.session.commit()

        return jsonify({'message' : 'Your password has been updated!'})
    
    except jwt.ExpiredSignatureError as error:
        print (error)
        return jsonify({'message' : "The link has expired"}), 400
       
    
if __name__ == '__main__':
    app.run()

