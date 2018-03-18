from flask import Flask ,render_template,session,redirect,url_for,flash
from flask_script import Manager,Shell
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField
from wtforms.validators import Required
from flask_sqlalchemy import SQLAlchemy
from string import ascii_uppercase


# render_template实现模板渲染，默认情况下在程序文件夹下的templates子文件夹中寻找模板
# render_template()第一个参数是模板的文件名，随后的参数都是键值对，表示模板中变量对应的真实值
# 
# Manager支持命令行参数 manage.run()
# 
# Bootstrap是客户端框架，不直接涉及服务器。服务器需要做的只是提供引用了Bootstrap的css和JavaScript文件的HTML响应，
# 并在html，css，javascript代码中实例化所需组件。需要在线加载模板
# 
# Flask-Moment把moment.js集成到jinja2模板中，在浏览器中渲染日期和时间，传入时间参数需要是utc时间
# Flask-Moment依赖moment.js和jquery.js
# Flask-Moment实现了moment.js中的format() fromNow() fromTime() calendar() valueOf() unix()方法
# 
# Flask-WTF，每个表单都由一个继承自Form的类表示。这个类定义表单中的一组字段，每个字段都用对象表示。
# 字段对象可附属多个验证函数。字段和验证函数直接从wtforms包中导入。
# 
# session,redirect,url_for实现重定向与用户会话。用户会话session是个字典，redirect实现重定向，url_for生成相对路径
# url_for()第一个参数是路由的内部名字，默认情况是相应视图函数的名字。
# 
# flash在表单上面显示一个消息，需要在模板渲染，使用get_flashed_messages()函数
# 
# 


app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string' #使用标准的dict语法 密匙应该保存在环境变量中
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:1996n8y13r@localhost:3306/Flask'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True#每次请求结束后会自动提交变动到数据库

manager = Manager(app) #把程序实例传入构造方法进行初始化
bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)


class NameForm(FlaskForm):#该表单包含一个文本字段和一个提交按钮
    name = StringField('What is your name?',validators=[Required()])#保证字段中有数据
    submit = SubmitField('Submit')

class Role(db.Model):
    __tablename__ = 'roles' #数据库中的表名
    id = db.Column(db.Integer,primary_key=True)#普通整数，主键
    name = db.Column(db.String(64),unique=True)#变长字符串，不允许出现重复值
    users = db.relationship('User',backref='role',lazy='dynamic')
    #第一个参数表明关系另一端的模型，第二个参数在User模型中添加role属性定义反向关系，第三个参数禁止自动执行查询

    def __repr__(self):
        return '<Role %r>'%self.name

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(64),unique=True,index=True)#为这列创建索引
    role_id = db.Column(db.Integer,db.ForeignKey('roles.id'))#外键 roles表中行的id

    def __repr__(self):
        return '<User %r>'%self.username

@app.route('/')
def index():
    return render_template('index.html',current_time=datetime.utcnow()) #服务器获得utc时间 .format('LLL')根据本地时区渲染时间 所以使用now()的话会多8个小时

@app.route('/user/<name>')
def user(name):
    return render_template('user.html',name=name) 

@app.route('/login',methods=['GET','POST'])#把这个视图函数注册成GET和POST请求的处理程序 提交表单大都作为POST请求进行处理
def loginform():
    #脑子有点抽 两个函数写的有点奇怪
    def da22(s):#处理用户名大小写 Walk_alan处理成_walk__alan 大写字母变_+小写字母 _变__
        l = []
        s1 = ''
        for i in s:
            if i in ascii_uppercase or i == '_':
                l.append('_')
                s1 += l[-1]
            l.append(i.lower())
            s1 += l[-1]
        return s1

    def da22recover(s): #与上一个函数功能相反 判断当前字符是否'_'以及后一字符
        l = []
        s1 = ''
        i = 0 
        while i < len(s):
            if s[i] == '_':
                if s[i+1] == '_':
                    s1 += '_'            
                else:
                    s1 += s[i+1].upper()
                i += 2
            else:
                s1 += s[i]
                i += 1
        return s1

    form = NameForm()
    if form.validate_on_submit():#判断提交的表 
    #第一次使用 .query. ...() 的时候会报错
        try:
            user = User.query.filter_by(username=form.name.data).first()#报错UnboundLocalError lib\site-packages\sqlalchemy\dialects\mysql\base.py 1578行val没有定义
        except UnboundLocalError:
            user = User.query.filter_by(username=form.name.data).first()#解决上一行的问题
        
        if user is None:#如果不能在数据库中找到对应姓名
            role_name = Role.query.filter_by(name='User').first()
            
            user = User(username=da22(form.name.data),role_id=role_name.id) #新人为用户
            db.session.add(user)
            db.session.commit()
            session['known'] = False 
        else:
            session['known'] = True
            #flash('Looks like you have changed your name!') #flashed_messages
        session['name'] = da22(form.name.data)
        form.name.data = ''
        return redirect(url_for('loginform')) #POST-重定向-GET模式 避免浏览器重复提交表单发出的警告
    return render_template('login.html',form=form,name=da22recover(session.get('name')),known=session.get('known',False))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'),404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'),500

#把对象添加到自动导入列表中，为shell命令注册一个make_context回调函数
def make_shell_context():
    return dict(app=app,db=db,User=User,Role=Role)
manager.add_command('shell',Shell(make_context=make_shell_context))

if __name__ == '__main__':
   app.run(debug=True) #manager.run() 调试数据库的时候用这个