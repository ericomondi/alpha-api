import sentry_sdk
from flask import request, jsonify
from sentry_sdk import capture_exception
from models import Product, app, db


sentry_sdk.init(
    dsn="https://b078e1ac4e38282ba56b7988cbdccc0a@us.sentry.io/4506695599849472",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)

db.create_all()

#Get all products and store product
@app.route("/products", methods=["POST", "GET", "PUT", "PATCH", "DELETE"])
def prods():
    if request.method == "GET":
        try:
            prods = Product.query.all()
            res = []
            for i in prods:
                res.append({"id": i.id,"name": i.name, "price": i.price })
            return jsonify(res), 200
        except Exception as e:
            # capture_exception(e)
            return jsonify({"Error" : str(e)}), 500
        
    elif request.method == "POST":
        if request.is_json:
           try:
                data = request.json
                new_data = Product(name=data['name'], price= data['price'])
                db.session.add(new_data)
                db.session.commit()
                r = f'Successfully stored product id: {str(new_data.id)}'
                res = {"Result" : r}
                return jsonify(res), 201
           except Exception as e:
                return jsonify({"Error" : str(e)}), 500
        else:
            return jsonify({"Error" : "Data is not json"}), 400 
    else:
        return jsonify({"Error" : "Method not allowed."}), 403
        
#Task by Thursday
#Get a single product in the route
#Create a new project call it alpha-app,make it boostrapand datatables enabled with dummy data(products) in a table
#Have a form in a bootstrap modal with products input
#Push your latest code. Create a new repo on github for alpha-app
        
