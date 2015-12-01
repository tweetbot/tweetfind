from flask import render_template, request
from app import app
import os
import retr

@app.route('/', methods=["GET"])
@app.route('/index', methods=["GET"])
def index():
    results=[]
    error=""
    if 'q' in request.args.keys():
        q = request.args['q'].strip()
        if(q != ''):
            results=retr.search(q,10)
            if len(results)==0:
                return render_template('noresults.html')
            else:
                return render_template('tfind.html',results=results)
        else:
            return render_template('base.html', error="Please Input a query")
    return render_template('base.html')
