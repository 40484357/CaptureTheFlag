from flask import Blueprint, render_template, request, redirect, url_for, flash
import hashlib, random, time, math
from . import db
from flask_login import login_user, login_required, current_user
from .models import users, phone_challenge, laptop_challenge, server_challenge, points
from datetime import date, datetime
from .utils import timeChange
from flask import Blueprint, render_template, request, redirect, url_for, flash, Markup
import hashlib, random, time, webbrowser
passwords = []
with open('CaptureTheFlag\webapp\static\cyberA-Z.txt') as f:
    words = f.readlines()
    passwords = [x.strip().lower() for x in words]


# Diffie-Hellman Key Exchange start
N = 604931 
G = 30672

# List of potential a and b values
possibleValues = [503, 521, 541, 557, 563, 613, 631, 641, 653, 661]
    
# Need to select two random unique values from the list
possibleValuesLength = len(possibleValues) - 1
primeSelection1 = random.randint(0, possibleValuesLength)
prime1 = possibleValues[primeSelection1]

# Remove the first value from the list and decrease the length of the list by 1
possibleValues.pop(primeSelection1)
possibleValuesLength -= 1

# Select the second value from the list
primeSelection2 = random.randint(0, possibleValuesLength)
prime2 = possibleValues[primeSelection2]
    
a = prime1 #variable
b = prime2 #variable
A = pow(G,a) % N
B = pow(G,b) % N
secretKey = pow(B,a) % N
print("A: ", A)
print("B: ", B)
print("Secret Key: ", secretKey)

views = Blueprint('views', __name__)

def pointsLogic(hintsUsed, userTime, totalPoints):
    basePoints = 50
    #timeLPenalty = (24 - round(timeLeft /3600))*500
    timeTaken = timeChange(userTime)
    timeTPenalty = timeTaken * 0.005
    hintPenalty = 0
    if(hintsUsed > 0):
        hintPenalty = basePoints - ((basePoints-timeTPenalty) * (1-(hintsUsed * 0.08)))
    finalPoints = basePoints - (hintPenalty + timeTPenalty)
    newPoints = math.ceil(totalPoints + finalPoints)
    return(newPoints)

@views.route('/laptop', methods=['GET', 'POST'])
def laptop():
    #database query for passkey, if it exists then that is the passkey otherwise generate and store new passkey
    passkey = db.session.query(laptop_challenge.laptopPassword).filter_by(user_id = current_user.id).first()
    challengeState = db.session.query(laptop_challenge.challengeState).filter_by(user_id = current_user.id).first()
    #checks challenge state, if it's 2 it will redirect the user to second challenge
    if challengeState:
        if challengeState[0] > 1:
            return redirect('/desktop')
    
    if passkey:
        print(passkey)
        selected = passkey[0]
        password = hashlib.md5(passkey[0].encode())
        
        print(password.hexdigest())
    else:
        passLength = len(passwords) - 1
        selection = random.randint(0, passLength) 
        selected = passwords[selection]
        password = hashlib.md5(selected.encode())
        beginTime = datetime.now()
        new_password = laptop_challenge(user_id = current_user.id, challengeState = 1, laptopPassword = selected, hints = 0, startTime = beginTime)
        db.session.add(new_password)
        db.session.commit()
        print(password.hexdigest())

    response = None
    if request.method=='POST':
        if request.form['answer'] != selected:
            response = 'wrong password, try again'
            flash(response)
        else:
            userChallenge = laptop_challenge.query.get_or_404(current_user.id)
            userChallenge.challengeState = 2
            userPoints = points.query.get_or_404(current_user.id)
            hintsUsed = db.session.query(laptop_challenge.hints).filter_by(user_id = current_user.id).first()
            time = db.session.query(laptop_challenge.startTime).filter_by(user_id = current_user.id).first()
            totalPoints= db.session.query(points.pointsTotal).filter_by(id = current_user.id).first()

            newPoints = pointsLogic( hintsUsed[0],time[0], totalPoints[0])
            userPoints.pointsTotal = newPoints #add new points total to DB
            db.session.commit()
            return redirect('/desktop')
            
    return render_template('laptop.html',password = password.hexdigest(), response = response)
    
@views.route('/desktop', methods=['GET', 'POST'])
def desktop():
    ip = "85.50.46.53"
    completed = 'false'
    userChallenge = laptop_challenge.query.get_or_404(current_user.id)
    challengeStateCheck = db.session.query(laptop_challenge.challengeState).filter_by(user_id = current_user.id).first()
    if(challengeStateCheck[0] == 1):
        return redirect('/laptop')
    elif(challengeStateCheck[0] >= 3):
        userChallenge.startTime = datetime.now()
        db.session.commit()
    else:
        userChallenge.challengeState = 3
        userChallenge.hints = 0
        userChallenge.startTime = datetime.now()
        db.session.commit()

    response = None
    if request.method == 'POST':
        if request.form['answer'] != ip:
            response = 'not quite try again'
            flash(response)
            return render_template('desktop.html', response = response)
            
        else:
            response = "That's the IP, but where does it go? " + ip
            completed = 'true'
            if(challengeStateCheck[0] ==3):
                userPoints = points.query.get_or_404(current_user.id)
                userChallenge.challengeState = 4
                hintsUsed = db.session.query(laptop_challenge.hints).filter_by(user_id = current_user.id).first()
                time = db.session.query(laptop_challenge.startTime).filter_by(user_id = current_user.id).first()
                totalPoints= db.session.query(points.pointsTotal).filter_by(id = current_user.id).first()
                newPoints = pointsLogic( hintsUsed[0],time[0], totalPoints[0])
                userPoints.pointsTotal = newPoints #add new points total to DB
                db.session.commit()
            flash(response)
            return render_template('desktop.html', response = response, completed = completed)

    return render_template('desktop.html', completed = completed)


@views.route('/phone', methods=['GET', 'POST'])
def phone():
    response = None
    primeA = db.session.query(phone_challenge.phonePrime1).filter_by(user_id = current_user.id).first()
    primeB = db.session.query(phone_challenge.phonePrime2).filter_by(user_id = current_user.id).first()
    challengeState = db.session.query(phone_challenge.challengeState).filter_by(user_id = current_user.id).first()

    if(challengeState):
        if(challengeState[0] == 2):
            return redirect('/phoneHome')

    if primeA:
        a = primeA[0] #variable
        b = primeB[0] #variable
        A = pow(G,a) % N
        B = pow(G,b) % N
        secretKey = pow(B,a) % N
        print("A: ", A)
        print("B: ", B)
        print("Secret Key: ", secretKey)
    else: 
        # Need to select two random unique values from the list
        possibleValuesLength = len(possibleValues) - 1
        primeSelection1 = random.randint(0, possibleValuesLength)
        prime1 = possibleValues[primeSelection1]

        # Remove the first value from the list and decrease the length of the list by 1
        possibleValues.pop(primeSelection1)
        possibleValuesLength -= 1

        # Select the second value from the list
        primeSelection2 = random.randint(0, possibleValuesLength)
        prime2 = possibleValues[primeSelection2]
            
        a = prime1 #variable
        b = prime2 #variable
        A = pow(G,a) % N
        B = pow(G,b) % N
        secretKey = pow(B,a) % N
        print("A: ", A)
        print("B: ", B)
        print("Secret Key: ", secretKey)
        new_phone_challenge = phone_challenge(user_id = current_user.id, challengeState = 1, phonePrime1 = a, phonePrime2 = b, hints = 0, startTime = datetime.now(), stegChallenge = 0, aesChallenge = 0 )
        db.session.add(new_phone_challenge)
        db.session.commit()

    if request.method=='POST':
        secretKeyGuess=request.form.get('answer', type=int)
        #secretKeyGuess = int(request.form['answer'])
        if secretKeyGuess != secretKey:
            response = 'wrong password, try again'
            print("secretKey: ", secretKey)
            print("secretKeyGuess: ", secretKeyGuess)
            flash(response)
        else:
            userChallenge = phone_challenge.query.get_or_404(current_user.id)
            userChallenge.challengeState = 2
            userPoints = points.query.get_or_404(current_user.id)
            hintsUsed = db.session.query(phone_challenge.hints).filter_by(user_id = current_user.id).first()
            time = db.session.query(phone_challenge.startTime).filter_by(user_id = current_user.id).first()
            totalPoints= db.session.query(points.pointsTotal).filter_by(id = current_user.id).first()
            newPoints = pointsLogic( hintsUsed[0],time[0], totalPoints[0])
            userPoints.pointsTotal = newPoints #add new points total to DB
            userChallenge.hints = 0
            db.session.commit()
            # Redirect to the next page
            return redirect(url_for('views.phoneHome'))
            
    return render_template('phone.html',password = secretKey,a=a,b=b, response = response)

@views.route('/phoneHome',methods =['GET','POST'])
def phoneHome():

    challengeState = db.session.query(phone_challenge.challengeState).filter_by(user_id = current_user.id).first()
    userChallenge = phone_challenge.query.get_or_404(current_user.id)
    userPoints = points.query.get_or_404(current_user.id)
    stegChallengeCheck = db.session.query(phone_challenge.stegChallenge).filter_by(user_id = current_user.id).first()

    if (challengeState == 1):
        return redirect('/phone')
    else: 
        userChallenge.startTime = datetime.now()

    aesState = 'false'

    if(stegChallengeCheck[0] == 1):
        aesState = 'true'
    

    response = None
    # Doing this because of two forms on one view, checks which one was used
    if request.method =='POST':
        if "validater" in request.form:
            if request.form['validatePhoto'] != "U2FsdGVkX18099HHwV0FYWBJXXfd4JDKkrhsHwGeD64=":
                response = 'Incorrect Ciphertext'
                flash(response)
            else:
                # assign chall 2 points, steganography
                
                if(stegChallengeCheck[0] == 0):
                    hintsUsed = db.session.query(phone_challenge.hints).filter_by(user_id = current_user.id).first()
                    time = db.session.query(phone_challenge.startTime).filter_by(user_id = current_user.id).first()
                    totalPoints= db.session.query(points.pointsTotal).filter_by(id = current_user.id).first()
                    newPoints = pointsLogic( hintsUsed[0],time[0], totalPoints[0])
                    userPoints.pointsTotal = newPoints #add new points total to DB
                    userChallenge.hints = 0
                    userChallenge.startTime = datetime.now()
                    userChallenge.stegChallenge = 1
                    db.session.commit()
                response = 'Correct Ciphertext.' 
                flash(response)
        elif "aes" in request.form:
            if request.form['password'] != "check_user.php":
                response = 'Incorrect password'
                flash(response)
                print('fail')
            else:
                # assign chall 3 points, aes
                response = Markup("Correct password.<br>Access Splunk <a href ='http://52.1.222.178:8000' target='_blank'>here</a><br>Username: ctf<br>Password: EscapeEscap3")
                aesChallengeCheck = db.session.query(phone_challenge.aesChallenge).filter_by(user_id = current_user.id).first()
                if(aesChallengeCheck[0] == 0):
                    print('success')
                    hintsUsed = db.session.query(phone_challenge.hints).filter_by(user_id = current_user.id).first()
                    time = db.session.query(phone_challenge.startTime).filter_by(user_id = current_user.id).first()
                    totalPoints= db.session.query(points.pointsTotal).filter_by(id = current_user.id).first()
                    newPoints = pointsLogic( hintsUsed[0],time[0], totalPoints[0])
                    userPoints.pointsTotal = newPoints #add new points total to DB
                    userChallenge.aesChallenge = 1
                    userChallenge.challengeState = 3
                    db.session.commit()
                flash(response)

    return render_template('phoneHome.html', aesState = aesState)     

@views.route('/server')
def server():
    return render_template('server.html')

@views.route('/login_wcg', methods = ['GET', 'POST'])
def login_wcg():
    flag = 'FLAG = static/robots.txt, view this page source in browser for next challenge'
    redir = "false"
    challenge3 = 'false'
    challengeText = ""
    challengeText2 = ""
    name = request.cookies.get('user')
    challengeState = db.session.query(server_challenge.challengeState).filter_by(user_id = current_user.id).first()
    if(challengeState[0] == 1):
        return redirect('/wickedcybergames')
    elif(challengeState[0] == 3 and name == 'admin'):
        challengeText = ['admin permissions verified', 'please validate the flag']
        challengeText2 = ['http://127.0.0.1:5000/static/cookie_admin.txt']
        challenge3 = 'true'
        response = 'verifying admin permissions'
        userChallenge = server_challenge.query.get_or_404(current_user.id)
        userChallenge.challengeState = 4
        db.session.commit()
        return render_template('login_wcg.html', flag = flag, redir = redir, challengeText = challengeText,  challengeText2 = challengeText2, challenge3 = challenge3)
    elif(challengeState[0] == 3):
        print(name)
        response = 'verify admin permissions... press enter to continue'
        challengeText = ['Admin not verified...','cookie user type None', 'Please verify admin state and refresh to continue']
        flash(response)
        redir = "true"
        return render_template('login_wcg.html', flag = flag, response = response, redir = redir, challengeText = challengeText, challenge3 = challenge3, challengeText2 = challengeText2)
    else:
        userChallenge = server_challenge.query.get_or_404(current_user.id)
        userChallenge.startTime = datetime.now()
        userChallenge.hints = 0
        db.session.commit()
    
    if request.method == 'POST':
        if request.form['flag_response'] == 'install':
            response = 'flag found, verify admin permissions... press enter to continue'
            answer = request.form['flag_response']
            challengeText = ['Admin not verified...','Checking cookie state...','user type None...' , 'Error: Inspect cookie, user type should be admin', 'Please verify admin state and refresh']
            flash(response)
            flash("FLAG = " + answer)
            redir = "true"
            userChallenge = server_challenge.query.get_or_404(current_user.id)
            userPoints = points.query.get_or_404(current_user.id)
            hintsUsed = db.session.query(server_challenge.hints).filter_by(user_id = current_user.id).first()
            time = db.session.query(server_challenge.startTime).filter_by(user_id = current_user.id).first()
            totalPoints= db.session.query(points.pointsTotal).filter_by(id = current_user.id).first()
            newPoints = pointsLogic( hintsUsed[0],time[0], totalPoints[0])
            userPoints.pointsTotal = newPoints #add new points total to DB
            userChallenge.startTime = datetime.now()
            userChallenge.hints = 0
            userChallenge.challengeState = 3
            db.session.commit()
            return render_template('login_wcg.html', flag = flag, response = response, answer = answer, redir = redir, challengeText = challengeText, challengeText2 = challengeText2, challenge3 = challenge3)
        elif request.form['flag_response'] == 'plugin':
            response = 'flag found, press enter to continue'
            challengeText = ['Flag: install-plugin', 'continue to splunk with flags', 'splunk link']
            flash(response)
            redir = 'true'
            userChallenge = server_challenge.query.get_or_404(current_user.id)
            userPoints = points.query.get_or_404(current_user.id)
            hintsUsed = db.session.query(server_challenge.hints).filter_by(user_id = current_user.id).first()
            time = db.session.query(server_challenge.startTime).filter_by(user_id = current_user.id).first()
            totalPoints= db.session.query(points.pointsTotal).filter_by(id = current_user.id).first()
            newPoints = pointsLogic( hintsUsed[0],time[0], totalPoints[0])
            userPoints.pointsTotal = newPoints #add new points total to DB
            userChallenge.startTime = datetime.now()
            userChallenge.challengeState = 4
            db.session.commit()
            return render_template('login_wcg.html', redir = redir, flag = flag, response = response, challenge3 = challenge3, challengeText = challengeText, challengeText2 = challengeText2)
        else: 
            response = 'incorrect flag, keep looking'
            answer = request.form['flag_response']
            print(answer)
            flash(response)
            flash(answer)
            return render_template('login_wcg.html', flag = flag, response = response, answer = answer, challengeText = challengeText, challengeText2 = challengeText2)

    return render_template('login_wcg.html', flag = flag, redir = redir, challenge3 = challenge3, challengeText = challengeText, challengeText2 = challengeText2)


@views.route('/wickedcybergames' , methods=['GET','POST'])
def wickedcybergames():
    challengeState = db.session.query(server_challenge.challengeState).filter_by(user_id = current_user.id).first()
    if(challengeState):
        if(challengeState[0] == 1):
            userChallenge = server_challenge.query.get_or_404(current_user.id)
            userChallenge.startTime = datetime.now()
            db.session.commit()
        elif(challengeState[0] == 2 | 3):
            return redirect('/login_wcg')
        elif(challengeState[0] == 4):
            return redirect('/login_wcg')
    else:
        new_server_challenge = server_challenge(user_id = current_user.id, challengeState = 1, startTime = datetime.now(), hints = 0)
        db.session.add(new_server_challenge)
        db.session.commit()

    response = None
    if request.method == 'POST':
        if request.form['username'] == 'admin':
            if request.form['password'] == 'IloveWickedGames2023':
                userChallenge = server_challenge.query.get_or_404(current_user.id)
                userPoints = points.query.get_or_404(current_user.id)
                print(userPoints)
                hintsUsed = db.session.query(server_challenge.hints).filter_by(user_id = current_user.id).first()
                time = db.session.query(server_challenge.startTime).filter_by(user_id = current_user.id).first()
                totalPoints= db.session.query(points.pointsTotal).filter_by(id = current_user.id).first()
                newPoints = pointsLogic( hintsUsed[0],time[0], totalPoints[0])
                userPoints.pointsTotal = newPoints #add new points total to DB
                userChallenge.startTime = datetime.now()
                userChallenge.hints = 0
                userChallenge.challengeState = 2
                db.session.commit()
                return redirect('/login_wcg')
            else: 
                response = 'wrong password'
        else: 
            response = 'wrong username'
            flash(response)
            return render_template('wickedcybergames.html', response = response)


    return render_template('wickedcybergames.html')

@views.route('/adminCheck', methods = ['GET', 'POST'])
def adminCheck():
    p1Text = None
    p2Text = None
    name = request.cookies.get('user')
    if request.method == 'POST':
        name = 'done'
        if request.form['username'] == 'admin':
            if request.form['password'] == 'plugin':
                print('successful login')
                p1Text = 'all details verified, game complete'
                p2Text = 'congratulations!'
            else: 
                p2Text = 'wrong password, try again'
        else:
            p1Text = 'wrong username or password, try again'

    if(name == 'admin'):
         p1Text = 'Admin Verified'
         p2Text = 'Please login with password to continue'
         webbrowser.open_new_tab('http://127.0.0.1:5000/static/cookie_admin.txt')
    elif(name == 'done'):
        print('done')
    else:
        p1Text = 'Error: Unverified Admin Login'
        p2Text = 'Cookies Display NoneType User...Please Check Details And Refresh The Page'
    
@views.route('/intro')
def intro():
    user_points = db.session.query(points.pointsTotal).filter_by(id = current_user.id).first()
    if user_points:
        return redirect('/cyberescape')
    return render_template('intro.html')

    