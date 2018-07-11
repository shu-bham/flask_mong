from flask import Flask,render_template,flash,redirect,url_for,logging,session,request,jsonify
from data import Articles
from flask_pymongo import PyMongo
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from pymongo import MongoClient
from bson.objectid import ObjectId
from functools import wraps


app = Flask(__name__)

# mongo = PyMongo(app)

# Articles = Articles()
@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    client = MongoClient('localhost:27017')
    db = client.new

    data = db.articles.find()

    if data.count()>0:
        return render_template('articles.html',articles = data)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html',msg = msg)
    

@app.route('/articles/<string:id>/')
def article(id):
    client = MongoClient('localhost:27017')
    db = client.new
    # ObId = db.ObjectId(id)
    res = db.articles.find_one({"_id":ObjectId(str(id))})
    
    return render_template('article.html',article = res)

class RegisterForm(Form):
    name = StringField('Name',[validators.Length(min=1,max=50)])
    username = StringField('Username',[validators.Length(min=4,max=25)])
    email = StringField('Email',[validators.Length(min=6,max=50)])
    password = PasswordField('Password',[
        validators.DataRequired(),
        validators.EqualTo('confirm',message = 'Password do not match')
    ])
    confirm = PasswordField('Confirm Password')

@app.route('/register',methods = ['GET','POST'])
def register():
    client = MongoClient('localhost:27017')
    db = client.new
    form = RegisterForm(request.form)
    
    if request.method == 'POST' and form.validate():
                
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(str(form.password.data)) 

        
        db.users.insert({
            'name' : name,
            'username' : username,
            'email' : email,
            'password' : password
        })
        client.close()
        flash('Form Submitted successfully','success')
        return redirect(url_for('register'))
        # return render_template('register.html')
    
    return render_template('register.html',form=form)

@app.route('/view')
def show():
    client = MongoClient('localhost:27017')
    db = client.new

    data = db.users.find()

    
    # return str(data[0])
    return render_template('view.html',data=data)

@app.route('/login',methods= ['GET','POST'])
def login():
    if request.method == 'POST':
        client = MongoClient('localhost:27017')
        db = client.new
        
        username = request.form['username']
        password = request.form['password']

        res = db.users.find({'username':username})
        # print (res.count())
        if res.count() > 0:
            print (res.count())
            data = db.users.find_one({'username':username},{'password':1}) 

            client.close()

            pwd = data['password']

            if sha256_crypt.verify(password,pwd):
                # app.logger.info("Password Match")
                session['logged_in'] = True
                session['username'] = username
                flash('SuccessFully Logged In','success')
                return redirect(url_for('dashboard'))
            else:
                error = "Password didn't match"
                return render_template('login.html',error=error)

        else:
            error = "No user found"
            return render_template('login.html',error=error)
        


    return render_template('login.html')

def is_logged_in(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in' in session:
            return f(*args,**kwargs)
        else:
            flash('Unauthorized Access','danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are successfully logged Out','success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@is_logged_in
def dashboard():
    client = MongoClient('localhost:27017')
    db = client.new

    data = db.articles.find()
    client.close()
    if data.count()>0:
        return render_template('dashboard.html',articles = data)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html',msg = msg)

class ArticleForm(Form):
    title = StringField('Title',[validators.Length(min=2,max=250)])
    body = TextAreaField('Body',[validators.Length(min=4)])
    
@app.route('/add_article',methods = ['GET','POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        client = MongoClient('localhost:27017')
        db = client.new

        db.articles.insert({
            "title" : title,
            "body"  : body,
            "author": session['username']
        })

        client.close()
        flash('Article Saved','success')
        return redirect(url_for('dashboard'))

    return render_template('add_article.html',form = form)

@app.route('/edit_article/<string:id>/',methods = ['GET','POST'])
@is_logged_in
def edit_article(id):
    client = MongoClient('localhost:27017')
    db = client.new

    res = db.articles.find_one({"_id":ObjectId(str(id))})

    form = ArticleForm(request.form)

    # print ('loggg',str(res['title']))
    form.title.data = res['title']
    form.body.data = res['body']



    if request.method == 'POST' and form.validate():
        
        
        # title = form.title.data
        # body = form.body.data

        title = request.form['title']
        body = request.form['body']


        # client = MongoClient('localhost:27017')
        # db = client.new

        db.articles.update({ "_id" :ObjectId(str(id))},
        { 
            '$set' : {
                "title" : title,
                "body"  : body
            }
        })

        # client.close()
        flash('Article Updated','success')
        return redirect(url_for('dashboard'))

    return render_template('edit_article.html',form = form)  

@app.route('/delete_article/<string:id>/',methods = ['POST'])
@is_logged_in
def delete_article(id):
    client = MongoClient('localhost:27017')
    db = client.new

    db.articles.remove({"_id":ObjectId(str(id))})

    flash('Article Deleted','success')
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.secret_key = 'my secrret key'
    app.run(debug = True)


















# from flask import Flask,request
# from flask_restful import Resource,Api

# app = Flask(__name__)
# api = Api(app)

# class HelloWorld(Resource):
#     def get(self):
#         return { 'about' : 'Hello World'}
#     def post(self):
#         some_json = request.get_json()
#         return {'you sent':some_json},201

# class multi(Resource):
#     def get(self,num):
#         return {'ans':num*10}

# api.add_resource(HelloWorld,'/')
# api.add_resource(multi,'/multi/<int:num>')

# if __name__ == '__main__':
#     app.run(debug=True)




























# from flask import Flask,jsonify,request

# app = Flask(__name__)

# @app.route('/',methods = ['GET','POST'])
# def index():
#     if request.method == 'POST':
#         some_json = request.get_json()
#         return jsonify({'you sent' : some_json}),201
#     else:
#         return jsonify({'about':'hello world'})

# @app.route('/multi/<int:num>',methods = ['GET'])
# def getmultiply10(num):
#     return jsonify({'result':num*10})


# if __name__ == '__main__':
#     app.run(debug=True)