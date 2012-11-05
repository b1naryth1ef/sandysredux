from flask import Flask, flash, render_template, request, redirect, url_for, session
from datetime import datetime
from data import Provider, School, Admin
import os, requests, smtplib, string, bcrypt

app = Flask(__name__)
app.secret_key = "asdfalsdkfg38asdfl38as8dfa8"
pword = os.getenv('SANDYLOGIN', 'test')
captcha_priv = os.getenv('CAPTCHAPRIV', None)

form_key = {
    1:['Boroughs you can support:', ["Bronx", 'Brooklyn', 'Manhattan', 'Queens', 'Staten Island'], False],
    2:['What type of support can you provide?', ['Furniture', 'Office Equipment', 'Office Supples', 'Classroom Materials', 'Art Supplies', 'Books', 'Art Residencies', 'Student Programs'], True],
    3:['Which grade levels is your support most appropriate?', ['All Grade Levels', 'Primary Grades', 'Elementary School', 'Middle School', 'High School'], False],
    4:['How will donations be delievered to schools?', ['US Mail', 'Other Mail Carriers', 'Truck/Courier Service', 'School Pickup'], True],
    5:['Is this donation being provided at NO cost to schools?', ['YES', 'NO'], True]}

f_db_key = {
    1:'locations',
    2:'support',
    3:'grade',
    4:'delivery',
    5:'cost'}

def hashPw(pw):
    return bcrypt.hashpw(pw, bcrypt.gensalt(12))

def checkPw(pw, hashed):
    return bcrypt.hashpw(pw, hashed) == hashed

def sendMail(to, id):
    subject = "Sandy School Support Submission Recieved"
    text = """
    We have recieved your submission to Sandy School Support! Thank you so much for you support!
    You submission reference number is: %s""" % id
    b = string.join((
            "From: %s" % "noreply@hydr0.com",
            "To: %s" % to,
            "Subject: %s" % subject,
            "",
            text
            ), "\r\n")
    server = smtplib.SMTP('localhost')
    server.sendmail("noreply@hydr0.com", [to], b)
    server.quit()

def isMod():
    return session.get('loggedin', False)

def render(*args, **kwargs):
    kwargs['ismod'] = isMod()
    return render_template(*args, **kwargs)

@app.template_filter('fid')
def templateFid(s):
    return s.replace(' ', '_').lower().strip()

#-- Static Routes --
@app.route('/login', methods=['POST'])
def routeLogin():
    u = Admin.objects(username=request.form.get('user')) 
    if len(u) and checkPw(request.form.get('pw'), u[0].password):
        session['loggedin'] = True
        flash('Welcome back %s!' % u[0].username, 'success')
        return redirect('/')
    flash('Invalid login details!', 'error')
    return redirect('/')

@app.route('/logout')
def routeLogout():
    session['loggedin'] = False
    return redirect('/')

@app.route('/')
def routeIndex(): return render('index.html')

@app.route('/school')
def routePost(): return render('post.html')

@app.route('/provider')
def routeProvide(): return render('help.html', form=form_key)

@app.route('/mod')
def routeMody():
    if not isMod():
        flash('You must be logged in to do that!', 'error')
        return redirect('/')
    return render('admin.html', users=Admin.objects())

@app.route('/mod/schools')
@app.route('/mod/schools/<page>')
@app.route('/mod/school/<id>')
def routeSchools(id=None, page=1):
    if not isMod():
        flash('You must be logged in to do that!', 'error')
        return redirect('/')
    if not id:
        try: r = School.objects().paginate(page=int(page), per_page=20)
        except: 
            flash("You've reached the end of schools listing!", 'warning')
            return redirect('/mod/schools/%s' % int(page)-1)
        return render('schools.html', schools=r)
    else:
        q = School.objects(id=id)
        if not len(q):
            flash("No school request with ID '%s'" % id)
            return redirect('/')
        return render('schools.html', s=q[0])

@app.route('/mod/providers')
@app.route('/mod/providers/<page>')
@app.route('/mod/provider/<id>')
def routeProviders(id=None, page=1):
    if not isMod():
        flash('You must be logged in to do that!', 'error')
        return redirect('/')
    if not id:
        try: r = Provider.objects().paginate(page=int(page), per_page=20)
        except: 
            flash("You've reached the end of providerss listing!", 'warning')
            return redirect('/mod/schools/%s' % int(page)-1)
        return render('providers.html', providers=r)
    else:
        q = Provider.objects(id=id)
        if not len(q):
            flash("No provider request with ID '%s'" % id)
            return redirect('/')
        return render('providers.html', p=q[0])

# -- Dynamic Stuffs --
@app.route('/mod/a/<action>', methods=['GET', 'POST'])
@app.route('/mod/a/<action>/<id>', methods=['GET', 'POST'])
def routeMod(id=None, action=None):
    if not isMod(): return redirect(url_for('/find'))
    if action == 'adduser':
        if request.form.get('user') and request.form.get('pw'):
            u = Admin(username=request.form.get('user'),
                    password=hashPw(request.form.get('pw')))
            u.save()
            flash('Added user "%s" successfully!' % request.form.get('user'), 'success')
            return redirect('/mod')
    elif action =='rmvuser':
        q = Admin.objects(id=id)
        if len(q):
            q[0].delete()
            flash('Deleted user successfully!', 'success')
            return redirect('/mod')
        flash('Error deleting user!', 'error')
        return redirect('/mod')
    if not id:
        flash('Error processing your request!', 'error')
        return redirect('/mod')
    act = action.split('_', 1)
    if act[-1] == 'provider':
        q = Provider.objects(id=id)
        text = 'submission'
        url = '/mod/provider'
    elif act[-1] == 'school':
        q = School.objects(id=id)
        text = 'request'
        url ='/mod/school'
    if not len(q):
        flash('Error processing your request! (Could not find %s)' % text, 'error')
        return redirect(url+'s')
    q = q[0]
    if act[0] == 'del':
        q.delete()
        flash('Deleted %s!' % text, 'success')
        return redirect(url+'s')
    elif act[0] == 'mark':
        q.active = False
        q.save()
        flash('Marked %s as done!' % text, 'success')
        return redirect(url+'/%s' % id)

@app.route('/internals/<route>', methods=['POST'])
def internals(route=None):
    if route == 'school':
        for k, v in request.form.items():
            if not v: 
                flash('No fields can be empty!', 'error')
                return redirect('/school')
        obj = School(
            contactname=request.form['name'],
            needs=request.form['request'],
            location=request.form['location'],
            schoolname=request.form['sname'],
            contactphone=request.form['phonenum'],
            contactemail=request.form['email'])
        obj.save()
        flash('Your request has been submitted to the system! Reference ID: "%s"' % obj.id, 'success')
        return redirect('/')

    elif route == "provider": #This would be horrible if we pushed this into heavy production (form injection)
        obj = Provider()
        for k in f_db_key.values():
            setattr(obj, k, [])
        val = form_key.keys()
        for k, v in request.form.items():
            if '_' in k:
                id, name = k.split('_', 1)
                if name == 'other' and request.form.get(k): 
                    name = 'Other: "%s"' % request.form.get(k)
                getattr(obj, f_db_key[int(id)]).append(name)
                if int(id) in val:
                    val.remove(int(id))
            else:
                if not v:
                    flash('All fields are required!', 'error')
                    return redirect('/provider')
        if len(val):
            flash("You must check at least ONE box in each section!")
            return redirect('/provider')

        obj.name = request.form['name']
        obj.title = request.form['title']
        obj.orgname = request.form['orgname']
        obj.email = request.form['email']
        obj.phone = request.form['phone']
        obj.timeframe = request.form['timeframe']
        obj.save()
        flash('Added your submission! Reference ID: "%s" (you may want to write this down)' % obj.id, 'success')
        return redirect('/')

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv('PORT', 5000)))
