from flask import jsonify
import sentry_sdk
from flask import flash, jsonify, request
from sentry_sdk import capture_exception
from flask_sqlalchemy import SQLAlchemy
from models import Product, app, db, Sale
from flask_cors import CORS
import requests
from sqlalchemy import func

sentry_sdk.init(
    dsn="https://b078e1ac4e38282ba56b7988cbdccc0a@us.sentry.io/4506695599849472",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)


# @app.before_first_request
# def create_tables():
#     db.create_all()


# store & store products
CORS(app)


@app.route("/products", methods=["POST", "GET"])
def prods():
    if request.method == "GET":
        try:
            prods = Product.query.all()
            p_dict = []
            for prod in prods:
                p_dict.append(
                    {"id": prod.id, "name": prod.name, "price": prod.price})
            return jsonify(p_dict)
        except Exception as e:
            print(e)
            # capture_exception(e)
            return jsonify({})

    elif request.method == "POST":
        if request.is_json:
            try:
                data = request.json
                new_product = Product(name=data.get(
                    'name'), price=data.get('price'))
                db.session.add(new_product)
                db.session.commit()
                r = "Product added successfully." + str(new_product.id)
                res = {"result": r}
                return jsonify(res), 201
            except Exception as e:
                print(e)
                # capture_exception(e)
                return jsonify({"error": "Internal Server Error"}), 500
        else:
            return jsonify({"error": "Data is not JSON."}), 400
    else:
        return jsonify({"error": "Method not allowed."}), 400

# Task by Thursday
# Get a single product in the route


@app.route('/get-product<int:product_id>', methods=['GET'])
def get_product(product_id):
    try:
        prd = Product.query.get(product_id)
        if prd:
            return jsonify({
                "id": prd.id,
                "name": prd.name,
                "price": prd.price
            })
        else:
            return jsonify({"error": "Product not found."}), 404
    except Exception as e:
        print(e)
        # capture_exception(e)
        return jsonify({"error": "Internal Server Error"}), 500


@app.route('/sales', methods=['GET', 'POST'])
def sales():
    if request.method == 'GET':
        try:
            sales = Sale.query.all()
            s_dict = []
            for sale in sales:
                s_dict.append({"id": sale.id, "pid": sale.pid,
                              "quantity": sale.quantity, "created_at": sale.created_at})
            return jsonify(s_dict)
        except Exception as e:
            print(e)
            # capture_exception(e)
            return jsonify({})

    elif request.method == 'POST':
        if request.is_json:
            try:
                data = request.json
                new_sale = Sale(pid=data.get(
                    'pid'), quantity=data.get('quantity'))
                db.session.add(new_sale)
                db.session.commit()
                s = "sales added successfully." + str(new_sale.id)
                sel = {"result": s}
                return jsonify(sel), 201
            except Exception as e:
                print(e)
                # capture_exception(e)
                return jsonify({"error": "Internal Server Error"}), 500
        else:
            return jsonify({"error": "Data is not JSON."}), 400
    else:
        return jsonify({"error": "Method not allowed."}), 400


@app.route('/dashboard', methods=["GET"])
def dashboard():

    # Query to get sales per day
    sales_per_day = db.session.query(
        # extracts date from created at
        func.date(Sale.created_at).label('date'),
        # calculate the total number of sales per day
        func.sum(Sale.quantity * Product.price).label('total_sales')
    ).join(Product).group_by(
        func.date(Sale.created_at)
    ).all()

    #  to JSON format
    sales_data = [{'date': str(day), 'total_sales': sales}
                  for day, sales in sales_per_day]
    #  sales per product
    sales_per_product = db.session.query(
        Product.name,
        func.sum(Sale.quantity*Product.price).label('sales_product')
    ).join(Sale).group_by(
        Product.name
    ).all()

    # to JSON format
    salesproduct_data = [{'name': name, 'sales_product': sales_product}
                         for name, sales_product in sales_per_product]

    return jsonify({'sales_data': sales_data, 'salesproduct_data': salesproduct_data})


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)