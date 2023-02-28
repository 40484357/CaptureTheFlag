from flask import Blueprint, render_template, request, redirect, url_for, flash
import hashlib, random
passwords = []
with open('webapp\static\cyberA-Z.txt') as f:
    words = f.readlines()
    passwords = [x.strip().lower() for x in words]

passLength = len(passwords) - 1
selection = random.randint(0, passLength)
selected = passwords[selection]
password = hashlib.md5(selected.encode())  

views = Blueprint('views', __name__)

@views.route('/')
def landing():
    passLength = len(passwords) - 1
    selection = random.randint(0, passLength)
    selected = passwords[selection]
    password = hashlib.md5(selected.encode())
    print(password.hexdigest())
    print(passLength)
    return render_template('cyberescape.html')

@views.route('/laptop', methods=['GET', 'POST'])
def laptop():
    print(selected)
    response = None
    if request.method=='POST':
        if request.form['answer'] != selected:
            response = 'wrong password, try again'
            flash(response)
        else:
            response = 'correct password'
            flash(response)
            
    return render_template('laptop.html',password = password.hexdigest(), response = response)
    


@views.route('/phone', methods=['GET', 'POST'])
def phone():
    N = 604931 
    G = 30672
    a = 593 #variable
    b = 821 #variable
    A = pow(G,a) % N
    B = pow(G,b) % N
    secretKey = pow(B,a) % N
    print("A: ", A)
    print("B: ", B)
    print("Secret Key: ", secretKey)
    response = None
    if request.method=='POST':
        if request.form['answer'] != secretKey:
            response = 'wrong password, try again'
            flash(response)
        else:
            response = 'correct password'
            flash(response)
    return render_template('phone.html',password = secretKey, response = response)

@views.route('/Points_Logic')
def points():
    return render_template('Points_Logic.html')
