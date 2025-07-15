from flask import Flask, render_template, url_for,request,session,redirect,make_response
from pymongo import MongoClient
import bcrypt
import re
import json
from datetime import timedelta

client=MongoClient("mongodb://localhost:27017/")
db=client["shop"]
collection_products=db["products"]
collection_carts=db["carts"]
collection_idcarts_products=db["idcart/product"]
collection_users=db["users"]

app=Flask(__name__)
app.secret_key="your_secret_key"
app.permanent_session_lifetime = timedelta(minutes=30)

upload_folder="/static/upload"
app.config["UPLOAD_FOLDER"]=upload_folder

@app.route('/')
def homepage():
    products = list(collection_products.find())  
    return render_template("dashboard.html",products=products)

@app.route('/login', methods=['POST','GET'])
def login():
    if request.method=='GET':
       return render_template('login.html')
    email=request.form.get("email","").strip()
    password=request.form.get("password","").strip()
    remember=request.form.get('remember','').strip()
    products = list(collection_products.find())  
    errors=[]
    user=collection_users.find_one({"ایمیل":email})
    if not email or not password:
       errors.append("پر کردن تمام فیلدها الزامی است!")
    if user:
       if not bcrypt.checkpw(password.encode('utf-8'), user['رمز عبور']) :
        errors.append(" رمز عبور وارد شده نادرست است")
    if email and not user:
       errors.append("ایمیل وارد شده نادرست است")
    if errors:
        print(errors)
        return render_template("login.html",errors=errors)
    session['user'] = email
    if remember:
       session.permanent = True
    else:
       session.permanent = False
    return redirect(url_for('buy'))

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='GET':
     return render_template("register.html")
    email=request.form.get('email','').strip()
    password=request.form.get('password','').strip()
    fullname=request.form.get('fullname','').strip()

    validemail=re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')
    validname=re.compile(r'^[\w\u0600-\u06FF\s]{2,50}$')
    validpassword=re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')
    errors=[]
    if collection_users.find_one({"ایمیل":email}):
       errors.append("این ایمیل قبلا ثبت نام شده است")
    if fullname and not validname.match(fullname):
       errors.append("فرمت نام وارد شده نادرست میباشد")
    if email and not validemail.match(email):
       errors.append("فرمت ایمیل وارد شده نادرست میباشد")
    if password and not validpassword.match(password):
       errors.append("رمز عبور تنظیم شده ناسازگار میباشد")
    if not fullname or not email or not password:
       errors.append("پر کردن تمام فیلدها الزامی است")

    if errors:
       print("فرم ارسال شد:", email, fullname)
       print("خطاها:", errors)
       return render_template("register.html",errors=errors)
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    document={
       "نام و نام خانوادگی":fullname,
       "ایمیل":email,
       "رمز عبور":hashed_password
    }

    collection_users.insert_one(document)
    return render_template("register.html",send=True)
@app.route('/dashboard')
def dashboard():
    products = list(collection_products.find())  
    return render_template("dashboard.html",products=products)
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
   products = list(collection_products.find()) 
   product=request.form.get('product','').strip()
   make_cookie=request.cookies.get('cart')
   cart=json.loads(make_cookie) if make_cookie else {}
   if product in cart:
      cart[product]+=1
   else:
      cart[product]=1
   res=make_response(render_template("dashboard.html",send=product,products=products))
   res.set_cookie('cart',json.dumps(cart))
   return res
@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
   products=list(collection_products.find())
   product=request.form.get('product')
   re_cookie=request.cookies.get('cart')
   cart=json.loads(re_cookie) if re_cookie else {}
   if product in cart:
      cart.pop(product)
   res=make_response(render_template('dashboard.html', rmv=product,products=products))
   res.set_cookie('cart',json.dumps(cart))
   return res
@app.route('/viewcart')
def viewcart():
   products=collection_products
   cart_cookie=request.cookies.get('cart')
   cart=json.loads(cart_cookie) if cart_cookie else {}
   total_price=0
   for p , q in cart.items():
      total_price+=q*products.find_one({"product":p}).get('price')
   return render_template('cart.html',cart=cart,products=products,total_price=total_price)
@app.route('/buy', methods=['POST', 'GET'])
def buy():
    if 'user' not in session:
        return redirect(url_for('login'))

    email = session['user']
    user = collection_users.find_one({'ایمیل': email})

    products = collection_products
    cart_cookie = request.cookies.get('cart')
    cart = json.loads(cart_cookie) if cart_cookie else {}
    total_price = 0
    for p, q in cart.items():
        total_price += q * products.find_one({"product": p}).get('price')

    if request.method == 'GET':
        return render_template('buy.html', cart=cart, user=user, total_price=total_price)

    if request.method == 'POST':
        card = request.form.get('card')
        password = request.form.get('password')
        CVV2 = request.form.get('CVV2')

        validcard = re.compile(r'\b\d{16}\b')
        validpassword = re.compile(r'\b\d{4,6}\b')
        validcvv2 = re.compile(r'\b\d{3,4}\b')

        errors = []

        if not card or not password or not CVV2:
            errors.append('پر کردن تمام فیلدها الزامی است')
        if not validcard.match(card) and card:
            errors.append('شماره کارت وارد شده نامعتبر است')
        if not validpassword.match(password) and password:
            errors.append('رمز دوم وارد شده نامعتبر است')
        if not validcvv2.match(CVV2) and CVV2:
            errors.append('CVV2 وارد شده نامعتبر است')

        if errors:
            return render_template('buy.html', errors=errors, user=user, cart=cart, total_price=total_price)

        document = {
            "نام کاربر": user.get('نام و نام خانوادگی'),
            'پست الکترونیک': email,
            "سفارش": cart
        }
        collection_carts.insert_one(document)

        response = make_response(render_template('buy.html', cart=cart, send=True, total_price=total_price, user=user))
        response.delete_cookie('cart')
        return response 
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('homepage'))

if __name__=="__main__":
    app.run(debug=True)