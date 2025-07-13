from flask import Flask, render_template, url_for,request,session,redirect,make_response
from pymongo import MongoClient
import bcrypt
import re
import json

client1=MongoClient("mongodb://localhost:27017/")
db1=client1["shop"]
collection_products=db1["products"]
collection_carts=db1["carts"]
collection_idcarts_products=db1["idcart/product"]

client2=MongoClient("mongodb://localhost:27017/")
db2=client2["users"]
collection_users=db2["users"]

app=Flask(__name__)
app.secret_key="your_secret_key"
upload_folder="/static/upload"
app.config["UPLOAD_FOLDER"]=upload_folder

@app.route('/')
def homepage():
    products = list(collection_products.find())  
    return render_template("dashbord.html",products=products)

@app.route('/login', methods=['POST'])
def login():
    email=request.form.get("email","").strip()
    password=request.form.get("password","").strip()
    products = list(collection_products.find())  
    errors=[]
    user=collection_users.find_one({"ایمیل":email})
    if user:
       if bcrypt.checkpw(password.encode('utf-8'), user['password']):
        session['user'] = email
        return render_template("dashbord.html",products=products)
    else:
       errors.append("ایمیل یا رمز عبور وارد شده نادرست است")
       return render_template("login.html",errors=errors)

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
       return render_template("register.html",errors=errors)
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    document={
       "نام و نام خانوادگی":fullname,
       "ایمیل":email,
       "رمز عبور":hashed_password
    }

    collection_users.insert_one(document)
    return render_template("register.html",send=True)
@app.route('/dashbord')
def dashbord():
    products = list(collection_products.find())  
    return render_template("dashbord.html",products=products)
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
   res=make_response(render_template("dashbord.html",send=product,products=products))
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
   res=make_response(render_template('dashbord.html', rmv=product,products=products))
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
@app.route('/logout')
def logout():
    products = list(collection_products.find())  
    return render_template("dashbord.html",products=products)

if __name__=="__main__":
    app.run(debug=True)