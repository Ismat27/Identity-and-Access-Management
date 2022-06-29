import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
# db_drop_and_create_all()

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['GET'])
def drinks():
    """Route for getting drinks
    """
    try:
        drinks = [
            drink.short() 
            for drink in  Drink.query.order_by(Drink.id).all()
        ]
    except Exception as e:
        abort(422)
    return jsonify({
        'success': True,
        'drinks': drinks
    }), 200

'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def drinks_details(payload):
    """Route for getting drinks details
    """
    try:
        drinks = [
            drink.long() 
            for drink in  Drink.query.order_by(Drink.id).all()
        ]
    except Exception as e:
        abort(422)

    return jsonify({
        'success': True,
        'drinks': drinks
    }), 200

'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def new_drink(payload):
    """Route for creating new drinks
    """
    data = request.get_json()

    title = data['title']
    recipe = data['recipe']
    print(title, recipe)
    if not title or not recipe:
        abort(400)

    new_drink = Drink(
        title=title,
        recipe=json.dumps(recipe)
    )
    print(new_drink)
    try:
        new_drink.insert()
        return jsonify({
            'success': True,
            'drinks': [new_drink.long()]

        }), 200
    except Exception as e:
        db.session.rollback()
        abort(422)
    finally:
        db.session.close()

'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drinks(payload, id):
    """Route for updating drinks
    """
    
    
    data = request.get_json()
    # title = data['title']
    # recipe = data['recipe']

    try:
        drink = Drink.query.get(id)

        if not drink:
            abort(404)

        if 'title' in data:
            drink.title = data['title']
        if 'recipe' in data:
            drink.recipe = json.dumps(data['recipe'])
        drink.update()

    except Exception as e:
        db.session.rollback()
        db.session.close()
        abort(422)

    return jsonify({
            'success': True,
            'drinks': [drink.long()]
        })

        
'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(payload, id):
    """Route for deleting drinks
    """
    drink = Drink.query.get(id)
    if not drink:
        abort(404)
    try:
        drink.delete()
    except Exception as e:
        db.session.rollback()
        abort(422)
    return jsonify({
        'success': True,
        'delete': id
    })

# Error Handling


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'message': 'bad request',
        'error': 400
    }), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'resource not found',
        'error': 404
    }), 404

@app.errorhandler(405)
def not_allowed(error):
    return jsonify({
        'success': False,
        'message': 'method not allowed',
        'error': 405
    }), 405

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        'success': False,
        'message': 'request is unprocessable',
        'error': 422
    }), 422

@app.errorhandler(AuthError)
def unauthorized(error):
    print(error)
    return jsonify({
        'success': False,
        'message': error.error,
        'error': error.status_code
    }), 403


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''


# https://coffee-tenant.us.auth0.com/authorize?audience=http://127.0.0.1:5000&response_type=token&client_id=dnavZyqgr3AIGsiiiHpsrdC0o73oHZGN&redirect_uri=http://127.0.0.1:8100