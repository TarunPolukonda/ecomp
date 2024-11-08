from flask import Flask,redirect,render_template,request,flash,url_for,session,Response
from flask_session import Session
import mysql.connector
from otp import genotp
from cmail import sendmail
from stoken import token,dtoken
import os,re
import razorpay
app=Flask(__name__)
app.config['SESSION_TYPE']='filesystem'
#config=pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
RAZORPAY_KEY_ID='rzp_test_c6m46TaGhi7qx3'
RAZORPAY_KEY_SECRET='fARQS1WX4v942Z4ayClkzUSZ'
client=razorpay.Client(auth=(RAZORPAY_KEY_ID,RAZORPAY_KEY_SECRET))
mydb=mysql.connector.connect(host='localhost',username='root',password='root',db='ecomm')
# user=os.environ.get('RDS_USERNAME')
# db=os.environ.get('RDS_DB_NAME')
# password=os.environ.get('RDS_PASSWORD')
# host=os.environ .get('RDS_HOSTNAME')
# port=os.environ.get('RDS_PORT')
# with mysql.connector.connect(host=host, password=password, db=db, user=user, port=port) as conn:
#     cursor = conn.cursor()
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS usercreate (
#             username VARCHAR(100) NOT NULL,
#             user_email VARCHAR(100) NOT NULL,
#             address TEXT NOT NULL,
#             password VARBINARY(20) NOT NULL,
#             gender ENUM('Male','Female') DEFAULT NULL,
#             PRIMARY KEY (user_email),
#             UNIQUE KEY username (username)
#         )
#     """)
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS admincreate (
#             email VARCHAR(50) NOT NULL,
#             username VARCHAR(100) NOT NULL,
#             password VARBINARY(10) NOT NULL,
#             address TEXT NOT NULL,
#             accept ENUM('on','off') DEFAULT NULL,
#             dp_image VARCHAR(50) DEFAULT NULL,
#             ph_no BIGINT DEFAULT NULL,
#             PRIMARY KEY (email),
#             UNIQUE KEY ph_no (ph_no)
#         )
#     """)
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS items (
#             item_id BINARY(16) NOT NULL,
#             item_name VARCHAR(255) NOT NULL,
#             quantity INT UNSIGNED DEFAULT NULL,
#             price DECIMAL(14,4) NOT NULL,
#             category ENUM('home_appliances','Electronics','Fashion','Grocery') DEFAULT NULL,
#             image_name VARCHAR(255) NOT NULL,
#             added_by VARCHAR(50) DEFAULT NULL,
#             description LONGTEXT,
#             PRIMARY KEY (item_id),
#             KEY added_by (added_by),
#             CONSTRAINT items_ibfk_1 FOREIGN KEY (added_by) REFERENCES admincreate (email) 
#             ON DELETE CASCADE ON UPDATE CASCADE
#         )
#     """)
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS reviews (
#             username VARCHAR(30) NOT NULL,
#             itemid BINARY(16) NOT NULL,
#             title TINYTEXT,
#             review TEXT,
#             rating INT DEFAULT NULL,
#             date DATETIME DEFAULT CURRENT_TIMESTAMP,
#             PRIMARY KEY (itemid, username),
#             KEY username (username),
#             CONSTRAINT reviews_ibfk_1 FOREIGN KEY (itemid) REFERENCES items (item_id) 
#             ON DELETE CASCADE ON UPDATE CASCADE,
#             CONSTRAINT reviews_ibfk_2 FOREIGN KEY (username) REFERENCES usercreate (user_email) 
#             ON DELETE CASCADE ON UPDATE CASCADE
#         )
#     """)
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS contact_us (
#             name VARCHAR(100) DEFAULT NULL,
#             email VARCHAR(100) DEFAULT NULL,
#             message TEXT
#         )
#     """)
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS orders (
#             orderid BIGINT NOT NULL AUTO_INCREMENT,
#             itemid BINARY(16) DEFAULT NULL,
#             item_name LONGTEXT,
#             qty INT DEFAULT NULL,
#             total_price BIGINT DEFAULT NULL,
#             user VARCHAR(100) DEFAULT NULL,
#             PRIMARY KEY (orderid),
#             KEY user (user),
#             KEY itemid (itemid),
#             CONSTRAINT orders_ibfk_1 FOREIGN KEY (user) REFERENCES usercreate (user_email),
#             CONSTRAINT orders_ibfk_2 FOREIGN KEY (itemid) REFERENCES items (item_id)
#         )
#     """)

# mydb=mysql.connector.connect(host='localhost',user='root',password='root',db='ecomm')
app.secret_key=b'\xb8\x9d\x0c\xaf'
@app.route('/')
def home():
    return render_template('welcome.html')
@app.route('/index')
def index():
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select bin_to_uuid(item_id),item_name,image_name,price,description,category,quantity from items')
    item_data=cursor.fetchall()
    print(item_data)
    return render_template('index.html',item_data=item_data)
@app.route('/admincreate',methods=['GET','POST'])
def admincreate():
    if request.method=='POST':
        username=request.form['name']
        email=request.form['email']
        password=request.form['password']
        address=request.form['address']
        accept=request.form['accept']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from admincreate where email=%s',[email])
        email_count=cursor.fetchone()[0]
        if email_count==0:
            otp=genotp()
            data={'username':username,'email':email,'password':password,'address':address,'otp':otp,'accept':accept}
            subject='Admin verify for BUYMORE'
            body=f'Use this otp for verification {otp}'
            sendmail(email=email,subject=subject,body=body)
            flash('Otp send successfully')
            return redirect(url_for('adminverify',var1=token(data=data)))
        elif email_count==1:
            flash('Email Already existed...')
            return redirect(url_for('adminlogin'))
        else:
            return 'something went wrong'
    return render_template('admincreate.html')
@app.route('/adminverify/<var1>',methods=['GET','POST'])
def adminverify(var1):
    try:
        regdata=dtoken(data=var1)
        print(regdata)
    except Exception as e:
        print(e)
        return 'Something went wrong'
    else:
        if request.method=='POST':
            uotp=request.form['otp']
            if uotp==regdata['otp']:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('insert into admincreate(email,username,password,address,accept) values(%s,%s,%s,%s,%s)',[regdata['email'],regdata['username'],regdata['password'],regdata['address'],regdata['accept']])
                mydb.commit()
                cursor.close()
                flash(f'{regdata["email"]} Registration successfully done')
                return redirect(url_for('adminlogin'))
            else:
                return 'Invalid otp'
            
    return render_template('otp.html')
@app.route('/adminlogin',methods=['GET','POST'])
def adminlogin():
    if session.get('uemail'):
        return redirect(url_for('adminpanel'))
    else:
        if request.method=='POST':
            email=request.form['email']
            password=request.form['password']
            password=password.encode('utf-8')
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(*) from admincreate where email=%s',[email])
            count=cursor.fetchone()
            print(count)
            if count:
                if count[0]==1:
                    cursor.execute('select password from admincreate where email=%s',[email])
                    dbpassword=cursor.fetchone()
                    if dbpassword:
                        if dbpassword[0]==password:
                            session['uemail']=email
                            if not session.get(email):
                                session[email]={}
                            return redirect(url_for('adminpanel'))
                        else:
                            flash('Wrong Password')
                    else:
                        flash('invalid Input for password')
                        return redirect(url_for('adminlogin'))
                else:
                    flash('wrong Email')
                    return redirect(url_for('admninlogin'))
            else:
                flash('Invalid Input for Email')
                return redirect(url_for('adminlogin'))
    return render_template('adminlogin.html')
@app.route('/adminpanel',methods=['GET','POST'])
def adminpanel():
    return render_template('adminpanel.html')
@app.route('/additems',methods=['GET','POST'])
def additem():
    if not session.get('email'):
        return redirect(url_for('adminlogin'))
    else:
        if request.method=='POST':
            item_name=request.form['Itemname']
            Description=request.form['description']
            price=request.form['price']
            quantity=request.form['quantity']
            category=request.form['Category']
            file=request.files['image']
            print(request.form)
            filename=genotp()+'.'+file.filename.split('.')[-1]
            print(filename)
            path=os.path.dirname(os.path.abspath(__file__))
            static_path=os.path.join(path,'static')
            file.save(os.path.join(static_path,filename))
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into items(item_id,item_name,description,price,quantity,image_name,added_by,category) values(uuid_to_bin(uuid()),%s,%s,%s,%s,%s,%s,%s)',[item_name,Description,price,quantity,filename,session.get('email'),category])
            mydb.commit()
            cursor.close()
            flash(f'Item {file} added successfully')
    return render_template('additem.html')
@app.route('/adminlogout')
def adminlogout():
    if session.get('email'):
        session.pop('email')
        return redirect(url_for('adminpanel'))
    else:
        return redirect(url_for('adminlogin'))
@app.route('/viewall_items')
def viewall_items():
    if not session.get('email'):
        return redirect(url_for('adminlogin'))
    else:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select bin_to_uuid(item_id),item_name,image_name,description from items where added_by=%s',[session.get('email')])
        item_data=cursor.fetchall()
        print(item_data)
        if item_data:
            return render_template('viewallitems.html',item_data=item_data)
        else:
            return 'No Items added...'
    return render_template('viewallitems.html')
@app.route('/view_item/<itemid>')
def view_item(itemid):
    if not session.get("email"):
        return redirect(url_for('adminlogin'))
    else:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select bin_to_uuid(item_id),item_name,image_name,price,quantity,category,description from itens where added_by=%s and item_id=uuid_to_bin(%s)',[session.get('email'),itemid])
        item_data=cursor.fetchone()
        if item_data:
            return render_template('view_items.html',item_data=item_data)
        else:
            return 'something went wrong'
    return render_template("view_item.html")
@app.route('/delete_item/<itemid>')
def delete_item(itemid):
    if not session.get('email'):
        return redirect(url_for('adminlogin'))
    else:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('delete from items where added_by=%s and item_id=uuid_to_bin(%s)',[session.get('email'),itemid])
        mydb.commit()
        cursor.close()
        return redirect(url_for('viewall_items'))
@app.route('/update_item/<itemid>',methods=['GET','POST'])
def update_item(itemid):
    if not session.get('email'):
        return redirect(url_for('email'))
    else:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select bin_to_uuid(item_id),item_name,image_name,price,quantity,category,description from items where added_by=%s and item_id=uuid_to_bin(%s)',[session.get('email'),itemid])
        item_data=cursor.fetchone()
        cursor.close()
        if request.method=="POST":
            item_name=request.form['Itemname']
            description=request.form['description']
            quantity=request.form['quantity']
            category=request.form['category']
            file=request.files['image']
            price=request.form['price']
            if file.filename=='':
                filename=item_data[2]
            else:
                filename=genotp()+'.'+file.filename.split('.')[-1]
                path=os.path.dirname(os.path.abspath(__file__))
                static_path=os.path.join(path,'static')
                os.remove(os.path.join(static_path,item_data[2]))
                file.save(os.path.join(static_path,filename))
            cursor=mydb.cursor(buffered=True)
            cursor.execute('update items set item_name=%s,description=%s,price=%s,quantity=%s,image_name=%s,category=%s,added_by=%s where added_by=%s and item_id=uuid_to_bin(%s)',[item_name,description,price,quantity,filename,category,session.get('email'),session.get('email'),itemid])
            mydb.commit()
            cursor.close()
            flash(f'item with {itemid} updated successfully...')
            print("Inner")
            return redirect(url_for('update_item',itemid=itemid))
                
        if item_data:
            print("Outer")
            return render_template('update_item.html',item_data=item_data)
        else:
            return "Something went wrong"
@app.route('/adminprofile_update',methods=['GET','POST'])
def adminprofile_update():
    if not session.get('email'):
        return redirect(url_for('login'))
    else:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select username,address,dp_image,ph_no from admincreate where email=%s',[session.get('email')])
        admin_data=cursor.fetchone()
        cursor.close()
        if request.method=='POST':
            username=request.form['username']
            address=request.form['address']
            ph_no=request.form['ph_no']
            image=request.files['profile']
            if image.filename=='':
                filename=admin_data[2]
            else:
                filename=genotp()+'.'+image.filename.split('.')[-1]
                path=os.path.dirname(os.path.abspath(__file__))
                static_path=os.path.join(static_path,admin_data[2])
                # if admin_data[2]:

                #     os.remove(os.path.join(static_path,admin_data[2]))
                image.save(os.path.join(static_path,filename))
            cursor=mydb.cursor(buffered=True)
            cursor.execute('update admincreate set username=%s,address=%s,dp_image=%s,ph_no=%s where email=%s',[username,address,filename,ph_no,session.get('email')])
            mydb.commit()
            cursor.close()
            flash(f'{session.get("email")} profile updated successfully')
            return redirect(url_for('adminprofile_update'))
        if admin_data:
            return render_template('adminprofile.html',admin_data=admin_data)
        else:
            return 'Something went wrong'
@app.route('/usercreate',methods=['GET','POST'])
def usercreate():
    if request.method=='POST':
        name=request.form['name']
        email=request.form['email']
        address=request.form['address']
        password=request.form['password']
        gender=request.form['gender']
        print(request.form)
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from usercreate where user_email=%s',[email])
        email_count=cursor.fetchone()[0]
        if email_count==0:
            otp=genotp()
            data={'name':name,'email':email,'password':password,'address':address,'gender':gender,'otp':otp}
            subject='User verify for Ecommerce'
            body=f'Use this otp for verification {otp}'
            sendmail(email=email,subject=subject,body=body)
            flash('OTP has been sent to given mail')
            return redirect(url_for('userverify',var1=token(data=data)))
        elif email_count==1:
            flash('Email already exists. Please Login')
            return redirect(url_for('userlogin'))
        else:
            return 'Something went wrong'
    return render_template('usercreate.html')
@app.route('/userverify/<var1>',methods=['GET','POST'])
def userverify(var1):
    try:
        regdata=dtoken(data=var1)
        print(regdata)
    except Exception as e:
        print(e)
        return 'Something went wrong'
    else:
        if request.method=='POST':
            uotp=request.form['otp']
            if uotp==regdata['otp']:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('insert into usercreate(user_email,username,password,address,gender) values(%s,%s,%s,%s,%s)',[regdata['email'],regdata['name'],regdata['password'],regdata['address'],regdata['gender']])
                mydb.commit()
                cursor.close()
                flash(f'{regdata["email"]} Registration successfully done')
                return redirect(url_for('userlogin'))
            else:
                return 'Invalid otp'
            
    return render_template('otp.html')
@app.route('/userlogin',methods=['GET','POST'])
def userlogin():
    if not session.get('uemail'):
        return redirect(url_for('panel'))
    else:
        if request.method=='POST':
            uemail=request.form['email']
            password=request.form['password']
            password=password.encode('utf-8')
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(*) from admincreate where email=%s',[uemail])
            count=cursor.fetchone()
            print(count)
            if count:
                if count[0]==1:
                    cursor.execute('select password from admincreate where email=%s',[uemail])
                    dbpassword=cursor.fetchone()
                    if dbpassword:
                        if dbpassword[0]==password:
                            session['uemail']=uemail
                            if not session.get('uemail'):
                                session[uemail]={}
                            return redirect(url_for('panel'))
                        else:
                            flash('Wrong Password')
                    else:
                        flash('invalid Input for password')
                        return redirect(url_for('userlogin'))
                else:
                    flash('wrong Email')
                    return redirect(url_for('userlogin'))
            else:
                flash('Invalid Input for Email')
                return redirect(url_for('userlogin'))
    return render_template('userlogin.html')

@app.route('/panel')
def panel():
    return render_template('index.html')
@app.route('/dashboard/<category>')
def dashboard(category):
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select bin_to_uuid(item_id),item_name,description,quantity,price,image_name,category from items where category=%s',[category])
    cursor.close()
    items_data=cursor.fetchall()
    print(items_data)
    if items_data:
        return render_template('dashboard.html',items_data=items_data)
    else:
        return 'items not found'
@app.route('/description/<itemid>')
def description(itemid):
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select bin_to_uuid(item_id),item_name,description,price,quantity,image_name from items where item_id=uuid_to_bin(%s)',[itemid])
    item_data=cursor.fetchone()
    cursor.close()
    if item_data:
        return render_template('description.html',item_data=item_data)
    else:
        return 'no item found'
@app.route('/addreview/<itemid>',methods=['GET','POST'])
def addreview(itemid):
    if session.get('uemail'):
        if request.method=='POST':
            title=request.form['title']
            description=request.form['description']
            rating=request.form['rating']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into reviews(username,itemid,title,review,rating) values(%s,uuid_to_bin(%s),%s,%s,%s)',[session.get('uemail'),itemid,title,description,rating])
            mydb.commit()
            cursor.close()
            
            return render_template('review.html',itemid=itemid)
    else:
        return redirect(url_for('userlogin'))
    return render_template('addreview.html')
@app.route('/readreview/<itemid>',methods=['GET','POST'])
def readreview(itemid):
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select * from reviews where itemid=uuid_to_bin(%s)',[itemid])
    data=cursor.fetchall()
    cursor.execute('select bin_to_uuid(item_id),item_name,description,price,category,image_name,quantity from items where item_id=uuid_to_bin(%s)',[itemid])
    item_data=cursor.fetchone()
    cursor.close()
    if item_data and data:
        return render_template('readreview.html',data=data,item_data=item_data)
    else:
        flash('No reviews found')
        return redirect(url_for('description',itemid=itemid))
@app.route('/addcart/<itemid>/<name>/<category>/<price>/<image>/<quantity>')
def addcart(itemid,name,category,price,image,quantity):
    if not session.get('uemail'):
        return redirect(url_for('userlogin'))
    else:
        print(session.get('uemail'))
        print("session",session)
        if itemid not in session['uemail']:
            session[session.get('uemail')][itemid]=[name,price,1,image,category]
            session.modified=True
            flash(f'{name} added to cart')
            return redirect(url_for('index'))
        session[session.get('uemail')][itemid][2]=+1
        flash('item already existed')
        return redirect(url_for('index'))
@app.route('/viewcart',methods=['GET','POST'])
def viewcart():
    if not session.get('uemail'):
        return redirect(url_for('userlogin'))
    if session.get(session.get('uemail')):
        items=session[session.get('uemail')]
        print("items are",items)
    else:
        items='empty'
    if items=='empty':
        return "No Products added to cart"
    return render_template('cart.html',items=items)    
@app.route('/remove/<itemid>')
def remove(itemid):
    print("remove",session[session.get('uemail')])
    if session.get('uemail'):
        print(session[session.get('uemail')])
        session[session.get('uemail')].pop(itemid)
        session.modified=True
        return redirect(url_for('viewcart'))
    return redirect(url_for('userlogin'))
@app.route("/userlogout")
def userlogout():
    if session.get('uemail'):
        session.pop('uemail')
        return redirect(url_for('index'))
    return redirect(url_for('userlogin'))
@app.route('/pay/<itemid>/<name>/<float:price>',methods=['GET','POST'])
def pay(itemid,name,price):
    try:
        if request.method=='POST':
            qyt=int(request.form['qyt'])
            amount=int(price*100*qyt) #convert price into paise
            total_price=amount*qyt
            print(f'creating payment for item:{itemid}, name:{name}, price:{price}')
            #create Razorpay orcer
            order=client.order.create({
                'amount':amount,
                'currency':'INR',
                'payment_capture':'1'  
            })
            print(f'order created: {order}')
            return render_template('pay.html',order=order,itemid=itemid,name=name,price=total_price,qyt=qyt)
        else:
            return 'enter quantity'
    except Exception as e:
        #log the error and return a 400 response
        print(f'Error creating order : {str(e)}')
        return str(e),400
@app.route('/success',methods=['GET','POST'])
def success():
    #extract payment details from the form
    payment_id=request.form.get('razorpay_payment_id')
    order_id=request.form.get('razorpay_order_id')
    signature=request.form.get('razorpay_signature')
    name=request.form.get('name')
    itemid=request.form.get('itemid')
    total_price=request.form.get('total_price')
    qyt=request.form.get('qyt')
    #verification process
    params_dict={
        'razorpay_order_id':order_id,
        'razorpay_payment_id':payment_id,
        'razorpay_signature':signature
    }
    try:
        client.utility.verify_payment_signature(params_dict)
        cursor=mydb.cursor(buffered=True)
        cursor.execute('insert into orders(itemid,item_name,total_price,user,qty) values(uuid_to_bin(%s),%s,%s,%s,%s)',[itemid,name,total_price,session.get('uemail'),qyt])
        mydb.commit()
        cursor.close()
        return redirect(url_for('orders'))
    except razorpay.errors.SignatureVerificationError:
        return 'Payment verification Failed',400
@app.route('/orders')
def orders():
    if session.get('uemail'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from orders where user=%s',[session.get('uemail')])
        user_orders=cursor.fetchall()
        return render_template('orders.html',user_orders=user_orders)
    else:
        return redirect(url_for('userlogin'))
@app.route('/search',methods=['GET','POST'])
def search():
    if request.method=='POST':
        name=request.form['search']
        strg=['A-za-z0-9']
        pattern=re.compile(f'{strg}',re.IGNORECASE)
        if (pattern.match(name)):
            cursor=mydb.cursor(buffered=True)
            query='select bin_to_uuid(item_id),item_name,description,price,category,image_name,quantity from items where item_name like %s or description like %s or price like %s or category like %s'
            search_pram=f'%{name}%'
            cursor.execute(query,[search_pram,search_pram,search_pram,search_pram])
            data=cursor.fetchall()
            return render_template('dashboard.html',items_data=data)
        else:
            flash('result not found')
    return render_template('index.html')
@app.route('/contactus',methods=['GET','POST'])
def contactus():
    if request.method=='POST':
        name=request.form['title']
        email=request.form['email']
        message=request.form['message']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('insert into contact_us values(%s,%s,%s)',[name,email,message])
        mydb.commit()
        cursor.close()
        return redirect(url_for('contactus'))
    return render_template('contactus.html')
'''@app.route('/invoice/ordid>.pdf')
def invoice(ordid):
    if session.get('uemail'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from orders where irid=%s',[ordid])
        orders=cursor.fetchone()
        username=orders[5]
        oname=orders[2]
        qty=orders[3]
        cost=orders[4]
        cursor.execute('select username,address,user_email from usercreate where user_email=%s',[username])
        data=cursor.fetchone()
        uname=data[0]
        uaddress=data[1]
        html=render_template('bill.html',uname=uname,uaddress=uaddress,oname=oname,qty=qty,cost=cost)
        pdf=pdfkit.from_string(html,False,configuration=config)
        response=Response(pdf,content_type='application/pdf')
        response.headers['Content-Disposition']='inline; filename=output.pdf'
        return response'''
@app.route('/viewcontactus')
def viewcontactus():
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select * from contact_us where email=%s',[session.get('uemail')])
    data=cursor.fetchall()
    cursor.close()
    return render_template('viewcontactus.html',data=data)
app.run(debug=True,use_reloader=True)