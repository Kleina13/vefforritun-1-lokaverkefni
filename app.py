# APP


from os import urandom
from flask import Flask, render_template as rend, url_for, request, session, redirect
from pymysql import *
from time import gmtime, strftime

def time():
	return strftime("%d-%m-%Y %H:%M", gmtime())

def con_login():
	with login_connection.cursor() as cursor:
		cursor.execute("SELECT * FROM user")
		return cursor.fetchall()

def con_forum(table=str):
	with forum_connection.cursor() as cursor:
		cursor.execute(f"SELECT * FROM {table}")
		return cursor.fetchall()

app = Flask(__name__)
app.secret_key = urandom(13)

login_connection = connect(host='tsuts.tskoli.is', port=3306, user='2208022210',
						   password='mypassword', database='2208022210_...', autocommit=True)
forum_connection = connect(host='tsuts.tskoli.is', port=3306, user='2208022210',
						   password='mypassword', database='2208022210_lokaverkefni_forum', autocommit=True)

@app.route('/', methods=['GET', 'POST'])
def index():
	users = con_login()
	posts = con_forum('posts')
	comments = con_forum('comments')

	if 'user' in session:
		user = session['user']
	else: 
		user = {"username":"none", "password":"none", "name":"none"}

	return rend('index.html', user=user, posts=posts, comments=comments)

@app.route('/write', methods=['GET', 'POST'])
def write_post():
	r = request.form
	error = False

	if 'user' not in session:
		return redirect(url_for('index'))

	posts = con_forum('posts')

	user = session['user']

	if request.method == 'POST':
		error = True
		
		if len(posts) != 0:
			with forum_connection.cursor() as cursor:
				cursor.execute(f"""INSERT INTO Posts (post_id, author_key, title, content, post_date) VALUES 
								(
									{int(posts[-1][0] + 1)},
									'{user['username']}', 
									'{r['title']}',
									'{r['content']}',
									'{time()}'
								);""")
		else:
			with forum_connection.cursor() as cursor:
				cursor.execute(f"""INSERT INTO Posts (post_id, author_key, title, content, post_date) VALUES 
								(
									{0},
									'{user['username']}', 
									'{r['title']}',
									'{r['content']}',
									'{time()}'
								);""")
		return redirect(url_for('index'))
	
	return rend('post.html', user=user, error=error)

@app.route('/delete_post/<int:id>')
def delete_post(id):
	if 'user' not in session:
		return redirect(url_for('index'))

	user = session['user']

	posts = con_forum('posts')

	if user['username'] == posts[id][1]:
		with forum_connection.cursor() as cursor:
			cursor.execute(f"""DELETE FROM Posts WHERE post_id='{id}';""")
			cursor.execute(f"""DELETE FROM Comments WHERE original_post_id='{id}';""")

	return redirect(url_for('index'))

@app.route('/write/<int:id>', methods=['GET', 'POST'])
def write_comment(id):
	r = request.form
	error = False

	if 'user' not in session:
		return redirect(url_for('index'))

	posts = con_forum('posts')

	if id > len(posts) - 1:
		return redirect(url_for('index'))

	user = session['user']

	if request.method == 'POST':
		error = True
		
		with forum_connection.cursor() as cursor:
			cursor.execute(f"""INSERT INTO Comments (original_post_id, author_key, content, post_date) VALUES 
							(
								{id},
								'{user['username']}',
								'{r['content']}',
								'{time()}'
							);""")
		return redirect(url_for('index'))
	
	return rend('comment.html', user=user, error=error)

@app.route('/delete_comment/<int:id>')
def delete_comment(id):
	if 'user' not in session:
		return redirect(url_for('index'))

	user = session['user']

	comments = con_forum('comments')

	for c in comments:
		if user['username'] == c[1]:
			if id == c[0]:
				with forum_connection.cursor() as cursor:
					cursor.execute(f"""DELETE FROM Comments WHERE original_post_id='{id}' 
					and author_key='{c[1]}'
					and post_date='{c[3]}'
					and content='{c[2]}';""")

	return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
	r = request.form
	error = False

	if 'user' in session: 
		return redirect(url_for('index'))

	users = con_login()

	if request.method == 'POST':
		error = True
		for u in users:
			if r['username'] == u[0]:
				if r['password'] == u[1]:
					session['user'] = {"username":u[0], "password":u[1], "name":u[2]}
					return redirect(url_for('index'))

	return rend('login.html', error=error)

@app.route('/logout')
def logout():
	if 'user' in session:
		session.pop('user')
	return redirect(url_for('index'))

@app.route('/newuser', methods=['GET', 'POST'])
def new_user():
	r = request.form
	error = False

	if 'user' in session:
		return redirect(url_for('index'))

	users = con_login()

	if request.method == 'POST':
		for u in users:
			if u[0] == r['username']:
				error = True
				return rend('new_user.html', error=error)
		
		if r['confirm'] != r['password']:
			error = True
			return rend('new_user.html', error=error)

		with login_connection.cursor() as cursor:
			cursor.execute(f"""INSERT INTO User (user, pass, nafn) VALUES
    						   ('{request.form['username']}', '{request.form['password']}', '{request.form['name']}');""")
		return redirect(url_for('login'))

	return rend('new_user.html', error=error)


@app.route('/profile')
def profile():
	if 'user' in session:
		user = session['user']
	else:
		return redirect(url_for('login'))

	return rend('profile.html', user=user)


# error <<<<<<<<<<<
@app.errorhandler(400)
def error400(error):
	return rend('error.html', error_type=400, error=error)
@app.errorhandler(401)
def error401(error):
	return rend('error.html', error_type=401, error=error)
@app.errorhandler(403)
def error403(error):
	return rend('error.html', error_type=403, error=error)
@app.errorhandler(404)
def error404(error):
	return rend('error.html', error_type=404, error=error)
@app.errorhandler(500)
def error500(error):
	return rend('error.html', error_type=500, error=error)
@app.errorhandler(502)
def error502(error):
	return rend('error.html', error_type=502, error=error)
@app.errorhandler(503)
def error503(error):
	return rend('error.html', error_type=503, error=error)
@app.errorhandler(504)
def error504(error):
	return rend('error.html', error_type=504, error=error)
# error <<<<<<<<<<<

if __name__ == "__main__":
	app.run(debug=True)
