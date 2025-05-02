from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################
@app.route("/health", methods=["GET"])
def health():
    return jsonify(dict(status="OK")), 200

@app.route("/count", methods=["GET"])
def count():
    """return length of list"""
    count = db.songs.count_documents({})
    return {"count": count}, 200

@app.route("/song", methods=["GET"])
def songs():
    all_songs = db.songs.find({})
    return json_util.dumps({"songs": all_songs}), 200

@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id):
    var_song = db.songs.find_one({"id": id})
    if not var_song:
        return jsonify({"Message": "Song not found"}), 404
    return json_util.dumps({"Yours song": var_song}), 200


@app.route("/song", methods=["POST"])
def create_song():
    rec_data = request.get_json()
    new_id = rec_data.get('id')

    # Check for existing picture with the same 
    existing_song = db.songs.find_one({"id": new_id})
    if existing_song:
        return jsonify({"Message": f"song with id {new_id} already present"}), 302
    
    result = db.songs.insert_one(rec_data)
    response_data = {"inserted id": result.inserted_id}
    return json_util.dumps(response_data), 201

@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    update_data = request.get_json()
    var_song = db.songs.find_one({"id": id})
    if not var_song:
        return jsonify({"Message": "Song not found"}), 404
    
    if not update_data:
        return jsonify({"error": "No data provided"}), 400
    

    result = db.songs.update_one(
            {"id": id},
            {"$set": update_data}
            )

    if result.modified_count == 0:
        return {"message": "song found, but nothing updated"}, 200
    else:
        return parse_json(db.songs.find_one({"id": id})), 201 
    
@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    result = db.songs.delete_one({"id": id})

    if result.deleted_count == 0:
        return {"message": "song not found"}, 404
    else:
        return "", 204