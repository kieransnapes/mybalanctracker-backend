from flask import Flask, jsonify
from flask_restful import Resource, Api, reqparse
from tinydb import TinyDB, Query
from flask_cors import CORS
import uuid
import coingecko
import json 

cg = coingecko.CoingeckoAPIWrapper()

app = Flask(__name__)
api = Api(app)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

parser = reqparse.RequestParser()
parser.add_argument('location', type=str, help='Where the balance is stored')
parser.add_argument('asset', type=str, help='The token ticker')
parser.add_argument('quantity', type=str, help='How many float as a string')
parser.add_argument('token_id', type=str, help='coingecko token id')
parser.add_argument('id', type=str, help='balance id')
parser.add_argument('new', type=dict)
parser.add_argument('old', type=dict)
parser.add_argument('symbols', action='append', help='list of token symbols')



db = TinyDB('db.json')


class BalanceList(Resource):
    def get(self):
        balances = db.all()
        return {'balances': balances}
    def post(self):
        args = parser.parse_args()
        item_id = str(uuid.uuid4())
        token_id = args.get('token_id', None)
        balance_id = db.insert({'id':item_id, 'location': args['location'], 'asset': args['asset'], 'quantity': args['quantity'], 'token_id': token_id})
        return item_id, 201
    def put(self):
        q = Query()
        args = parser.parse_args()
        balance_id = db.update({'quantity': args['quantity']}, (q.id==args['id']))
        return balance_id, 204

class BalanceSummary(Resource):
    def get(self):
        balances = db.all()
        balance_groups= {}
        for balance in balances:
            if balance['asset'].upper() in balance_groups:
                balance_groups[balance['asset'].upper()]['balances'].append(balance)
            else:
                summary = {}
                summary['balances'] = [balance]
                summary['token_id'] = balance.get('token_id', None)
                balance_groups[balance['asset'].upper()] = summary

        summary = []
        for key, value in balance_groups.items():
            summary.append({'asset': key, 'balances':value['balances'], 'token_id':value['token_id']})
        return summary

class Asset(Resource):
    def delete(self, asset_id):
        q = Query()
        db.remove(q.token_id==asset_id)


class Balance(Resource):
    def delete(self, balance_id):
        q = Query()
        # args = parser.parse_args()
        db.remove(q.id==balance_id)

        return '', 204

class CoinList(Resource):
    def get(self):
        coins = cg.get_all_coins()
        return jsonify(coins)    
    def post(self):
        args = parser.parse_args()
        prices = cg.get_multiple_prices_by_symbols(args['symbols'])
        return jsonify(prices)

class Coin(Resource):
    def get(self, symbol):
        coin = cg.get_price_by_symbol(symbol)
        return jsonify(coin)   
    
api.add_resource(BalanceList, '/balances')
api.add_resource(BalanceSummary, '/balances/summary/')
api.add_resource(Asset, '/asset/<asset_id>/')
api.add_resource(Balance, '/balance/<balance_id>')
api.add_resource(CoinList, '/coins')
api.add_resource(Coin, '/coin/<symbol>')

if __name__ == '__main__':
    app.run(debug=True)