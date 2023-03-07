# save this as app.py
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user = db.Column(db.String(200), nullable = True)
    content = db.Column(db.String(500), nullable = True)
    created_at = db.Column(db.DateTime(), default= datetime.utcnow)


'''
@app.route("/create")
def create():
    db.create_all()
    return "DB created"
'''

@app.route("/<name>", methods=['GET','POST'])
def start_page(name):
    if request.method == 'POST':
        new_message = Message(
            user = name,
            content = request.form['content']
        )
        db.session.add(new_message)
        db.session.commit()
    return render_template('index.html')




if __name__ == "__main__":
    app.run(debug=True)

