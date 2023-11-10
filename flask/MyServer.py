import os
from flask import Flask, jsonify, request,render_template, redirect
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__, static_url_path='/static')
CORS(app)

client = MongoClient("mongo:27017")
machines_db = client['test1']
machines = machines_db['testMch']


## =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- #
## Pages
# @app.route('/loginPage')
# def login_page():
#     return render_template("login.html")

@app.route('/register')
def register():
   return render_template('register.html')

# @app.route('/registerComplete')
# def registerComplete():
#    return render_template('RegisterComplete.html')  

# @app.route('/voteFail')
# def voteFail():
#    return render_template('voteFail.html')

# @app.route('/voteComplete')
# def voteComplete():
#    return render_template('voteComplete.html')
   
@app.route('/')
def home():
   return render_template('index.html')

# @app.route('/voteDisplay')
# def voteDisplay():
#    return render_template('VoteDisplay.html')

# @app.route('/showVotesDisplay')
# def showVoteDisplay():
#    return render_template('ShowVotesDisplay.html')

## =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- #
## Debug
@app.route('/database')
def todo():
    try:
        client.admin.command('ismaster')
    except:
        return "Server not available"
    return "Hello from the MongoDB client!\n" + str(client.list_database_names()) #+ "\n" + str(logins.insert_many(data))

# ## =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- #
# ## Users
@app.route('/machines', methods=['GET'])
def get_users():
    mylist = machines.find()
    resp = list(mylist)
    return jsonify(resp)
# def create_user():
#     new_machine = request.form.to_dict()
#     new_machine["_id"] = new_machine["ip"] 
#     result = votes.insert_one({'_id': new_machine["ip"],"comunity":new_machine["color"],"refresh":new_machine[""]}) 

#     return redirect("/registerComplete")

@app.route('/regMachine', methods=['POST'])
def create_machine():
    new_machine = request.form.to_dict()

    new_machine["_id"] = new_machine["ip"] 
    result = machines.insert_one({'_id': new_machine["ip"],"comunity":new_machine["comunity"],"refresh":new_machine["refreshRate"]}) 

    return redirect("/")


# @app.route('/kill', methods=['POST'])
# def kill():
#     killHim = request.get_json()
    
#     if '_id' in killHim:
#         person_id = killHim['_id']

#         # Find the person by their ID and increment their vote
#         result = logins.find_one_and_update(
#             {"_id": person_id},
#             {"$set": {"is_dead": True}},
#             return_document=True
#         )

#         # Find the person by their ID and increment their vote
#         result2 = votes.find_one_and_update(
#             {"_id": person_id},
#             {"$set": {"is_dead": True}},
#             return_document=True
#         )

#         if result and result2:
#             return "Congrats", 200
#         else:
#             return jsonify({"error": "Person not found."}), 404
#     else:
#         return jsonify({"error": "Invalid data format."}), 400
# ## =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- #
# ## Reunion
# @app.route('/startReunion', methods=['GET'])
# def start_Reunion():
#     votes.update_many({}, {"$set": {"vote_count": 0}})
#     return redirect("/voteDisplay")

# @app.route('/voteOn', methods=['POST'])
# def make_vote():
#     new_vote = request.get_json()
    

#     if '_id' in new_vote and 'increment' in new_vote:
#         person_id = new_vote['_id']
#         increment = new_vote['increment']

#         # Find the person by their ID and increment their vote
#         result = votes.find_one_and_update(
#             {"_id": person_id},
#             {"$inc": {"vote_count": increment}},
#             return_document=True
#         )

#         if result:
#             return "Congrats", 200
#         else:
#             return redirect("/voteFail")
#     else:
#         return redirect("/voteFail")

# @app.route('/loginVote', methods=['POST'])
# def login_vote():
#     user = request.form.to_dict()
#     if logins.find_one({'_id': user["name"]})["psw"] == user["psw"]:
#         return redirect("/vote/"+user["name"])
#     else: 
#         return redirect("/loginPage")

# @app.route('/vote/<string:username>')
# def vote(username):
#    return render_template('vote.html',username=username)

# @app.route('/KillTarget/<string:username>')
# def killTarget(username):
#     # Find the person by their ID and increment their vote
#         result = logins.find_one_and_update(
#             {"_id": username},
#             {"$set": {"is_dead": True}},
#             return_document=True
#         )

#         # Find the person by their ID and increment their vote
#         result2 = votes.find_one_and_update(
#             {"_id": username},
#             {"$set": {"is_dead": True}},
#             return_document=True
#         )

#         if result and result2:
#             return "Congrats", 200
#         else:
#             return jsonify({"error": "Person not found."}), 404
   

# @app.route('/getVotes', methods=['GET'])
# def get_votes():
#     mylist = votes.find()
#     resp = list(mylist)

#     return jsonify(resp)

if __name__ == '__main__':
    app.run(host= "0.0.0.0",port=os.environ.get("FLASK_SERVER_PORT", 9090), debug=True)