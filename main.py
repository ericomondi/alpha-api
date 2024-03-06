from flask import jsonify
import sentry_sdk
from flask import flash, jsonify, request, make_response
from sentry_sdk import capture_exception
from flask_sqlalchemy import SQLAlchemy
from models import Product, app, db, Sale, User

from flask_cors import CORS
import requests
from sqlalchemy import func
import jwt 
from sqlalchemy import func,desc
from functools import wraps
import datetime
import uuid
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash



sentry_sdk.init(
    dsn="https://b078e1ac4e38282ba56b7988cbdccc0a@us.sentry.io/4506695599849472",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)


CORS(app)
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(public_id=data['public_id']).first()
            if not current_user:
                raise Exception('User not found')
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401
        except Exception as e:
            return jsonify({'message': str(e)}), 401

        return f(current_user, *args, **kwargs)

    return decorated



# def token_required(f):
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         token = request.headers.get('x-access-token')
#         print(token)

#         if not token:
#             return jsonify({'message': 'Token is missing!'}), 401

#         try:
#             data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
#             current_user = User.query.filter_by(public_id=data['public_id']).first()
#             if not current_user:
#                 raise Exception('User not found')
#         except jwt.ExpiredSignatureError:
#             return jsonify({'message': 'Token has expired!'}), 401
#         except jwt.InvalidTokenError:
#             return jsonify({'message': 'Invalid token!'}), 401
#         except Exception as e:
#             return jsonify({'message': str(e)}), 401

#         return f(current_user, *args, **kwargs)

#     return decorated



@app.route("/products", methods=["POST", "GET"])
@token_required
def prods(current_user):
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


@app.route('/get-product<int:product_id>', methods=['GET'])
@token_required
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
@token_required
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

@app.route('/register', methods=['POST'])
def register():
    data = request.json

    name = data.get('username')
    password = data.get('password')

    if not name or not password:
        return jsonify({'message': 'Name and password are required!'}), 400

    # Generate public_id
    public_id = str(uuid.uuid4())

    # Create new user
    hashed_password = generate_password_hash(password)
    new_user = User(public_id=public_id, name=name, password=hashed_password, admin=False)

    try:
        # Add new user to the database
        db.session.add(new_user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': 'User with this name already exists!'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'An error occurred while registering user', 'error': str(e)}), 500

    return jsonify({'message': 'New user created!'}), 200






# @app.route('/login', methods=['POST'])
# def login():
#     auth = request.json
#     print(auth)
#     if not auth or not auth.get('username') or not auth.get('password'):
#         return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

#     user = User.query.filter_by(name=auth.get('username')).first()

#     if not user:
#         return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

#     if check_password_hash(user.password, auth.get('password')):
#         token = jwt.encode({'public_id' : user.public_id, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
#         print(token)
#         return jsonify({'token' : token}), 200

#     return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})






@app.route('/login', methods=['POST'])
def login():
    auth = request.json
    print(auth)
    if not auth or not auth.get('username') or not auth.get('password'):
        return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

    user = User.query.filter_by(name=auth.get('username')).first()

    if not user:
        return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

    if check_password_hash(user.password, auth.get('password')):
        token = jwt.encode({'public_id' : user.public_id, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'], algorithm="HS256")
        print(token)

        # Decode and print the token
        try:
            decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])            
            print("Decoded Token:", decoded_token)
        except jwt.ExpiredSignatureError:
            print("Token has expired.")
        except jwt.InvalidTokenError as e:
            print("Invalid token:", e)
            # You can print additional details such as the token itself for debugging purposes
            print("Invalid token:", token)

        return jsonify({'token' : token}), 200








# @app.route('/login', methods=['POST'])
# def login():
#     auth = request.get_json()

#     if not auth or not auth.get('username') or not auth.get('password'):
#         return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

#     user = User.query.filter_by(name=auth.get('username')).first()

#     if not user or not check_password_hash(user.password, auth.get('password')):
#         return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

#     token = jwt.encode({'public_id' : user.public_id, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])

#     # Create a response with CORS headers
#     response = make_response(jsonify({'token' : token}), 200)
#     response.headers['Access-Control-Allow-Origin'] = 'http://127.0.0.1:5500'
#     response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'

#     return response



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)