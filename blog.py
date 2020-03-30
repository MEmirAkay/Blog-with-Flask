from flask import Flask,render_template,flash,redirect,url_for,logging,request,session
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps


#User Registration
class RegisterForm(Form):
    name = StringField("İsim Soyisim", validators=[validators.Length(min=3,max=25)])
    username = StringField("Kullanıcı Adı", validators=[validators.Length(min=8,max=25)])
    email = StringField("E-Mail", validators=[validators.Length(min=4,max=35),validators.Email(message="Lütfen geçerli bir mail adresi girin!")])
    password = PasswordField("Şifre", validators = [
        validators.DataRequired(message="Lütfen Bir şifre belirleyin!"),
        validators.EqualTo(fieldname= "confirm",message="Parolanız uyuşmuyor!")
    ])
    confirm = PasswordField("Parola Doğrula")



#User Login Check
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Sayfayı görüntülemek için giriş yapmalısınız..!","danger")
            return redirect(url_for("login"))    
    return decorated_function


#User Login
class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Şifre")


app = Flask(__name__)
app.secret_key = "emirblog"
app.config["MYSQL_HOST"]= "localhost"
app.config["MYSQL_USER"]= "root"
app.config["MYSQL_PASSWORD"]= "12345678"
app.config["MYSQL_DB"]= "emirblog"
app.config["MYSQL_CURSORCLASS"]= "DictCursor"
mysql = MySQL(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")


#Register
@app.route("/register",methods = ["GET","POST"])
def register():
    
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)
        
        cursor = mysql.connection.cursor()

        sorgu = "INSERT into users(name,email,username,password) VALUES(%s,%s,%s,%s)"

        cursor.execute(sorgu,(name,email,username,password))

        mysql.connection.commit()

        cursor.close()

        flash("İşlem Başarılı","success")

        return redirect(url_for("login"))
        
    else:
        return render_template("register.html", form= form)




@app.route("/login", methods = ["GET","POST"])
def login():
    form = LoginForm(request.form)
   
    if request.method == "POST":
        username = form.username.data
        pswrd_entered = form.password.data        
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM users where username = %s"

        result = cursor.execute(sorgu,(username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(pswrd_entered,real_password):
                flash("Giriş Başarılı!","success")

                session["logged_in"] = True
                session["username"] = username


                return redirect(url_for("index"))
            else:
                flash("Şifre Yanlış","danger")
                return redirect(url_for("login"))

        else:
            flash("Yanlış Kullanıcı adı","danger")
            return redirect(url_for("login.html"))

    return render_template("login.html", form = form)

@app.route("/article/<string:id>")
def detail(id):
    return "Article Id:"+id

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles where author = %s"
    result = cursor.execute(sorgu,(session["username"],))
    
    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)
    else:
        return render_template("dashboard.html")

    return render_template("dashboard.html")
#AddArticle
@app.route("/addarticle",methods = ["GET","POST"])
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data
        

        cursor = mysql.connection.cursor()
        sorgu = "INSERT INTO articles(title,author,content) VALUES(%s,%s,%s)"

        cursor.execute(sorgu,(title,session["username"],content,))

        mysql.connection.commit()

        cursor.close()

        flash("Makale Başarıyla yüklendi...","success")

        return redirect(url_for("index"))

    return render_template("addarticle.html",form = form)

#DetailPage
@app.route("/articles/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles where id = %s"
    result = cursor.execute(sorgu,(id,))

    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html",article=article)
    else:
        return render_template("article.html")

#UpdateArticle
@app.route("/update/<string:id>",methods = ["GET","POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM articles where id = %s and author = %s"
        result = cursor.execute(sorgu,(id,session["username"]))

        if result==0:
            flash("Böyle bir makale bulunamamakta.")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleForm()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html",form = form)
    else:
        #POST REQUEST
        form = ArticleForm(request.form)
        newTitle = form.title.data
        newContent = form.content.data

        sorgu2 = "UPDATE articles SET title = %s, content = %s where id = %s"

        cursor = mysql.connection.cursor()

        cursor.execute(sorgu2,(newTitle,newContent,id))
        mysql.connection.commit()
        
        flash("Makale başarıyla güncellendi","success")

        return redirect(url_for("dashboard"))

        
    


#DeleteArticle
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM articles where author = %s and id = %s"
    result = cursor.execute(sorgu,(session["username"],id))

    if result > 0:
        sorgu2 = "Delete from articles where id = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        flash("Silme işlemi başarılı...","success")
        return redirect(url_for("dashboard"))
    else:
        return redirect(url_for("index"))

#Article
class ArticleForm(Form):
    title = StringField("Başlık",validators=[validators.Length(min = 5, max = 100)])
    content = TextAreaField("İçerik",validators=[validators.Length(min = 10)])

@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles"
    result = cursor.execute(sorgu)

    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html",articles = articles)
    else:
        return render_template("articles.html")
#Search
@app.route("/search",methods=["GET","POST"])
def search():
    
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM articles where title like '%"+ keyword + "%'"

        result = cursor.execute(sorgu)

        if  result == 0:
            flash("Sonuç bulunamadı.","warning")
            return redirect(url_for("articles"))
        else:
            articles = cursor.fetchall()

            return render_template("articles.html",articles=articles)
    
if __name__ == "__main__":
    app.run(debug=True)
