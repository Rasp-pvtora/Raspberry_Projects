from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
import database
import analytics
import config

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = config.JWT_SECRET
jwt = JWTManager(app)

conn = database.init_db()  # Shared conn (or per-request)

# Login route (stub; add user auth)
@app.route('/login', methods=['POST'])
def login():
    # Validate user/pass; for demo, any
    token = create_access_token(identity='operator')
    return jsonify(access_token=token)

@app.route('/add_owner', methods=['POST'])
@jwt_required()
def add_owner():
    data = request.json
    database.update_owner_details(conn, data['plate_number'], data['name'], data['surname'], data['address'])
    return jsonify({'status': 'updated'})

@app.route('/add_watchlist', methods=['POST'])
@jwt_required()
def add_watchlist():
    data = request.json
    database.add_to_watchlist(conn, data['plate_number'])
    return jsonify({'status': 'added'})

@app.route('/heatmap', methods=['GET'])
@jwt_required()
def get_heatmap():
    start = request.args.get('start', datetime.now().strftime('%Y-%m-%d 00:00:00'))
    end = request.args.get('end', datetime.now().strftime('%Y-%m-%d 23:59:59'))
    data = analytics.generate_heatmap(conn, start, end)
    return jsonify(data)

# Add dashboard HTML route if needed

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
