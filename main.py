from unittest import result
from pymongo import MongoClient
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = MongoClient('mongodb://localhost', 27017)
db = client["toilet"]
room_collection = db["room"]
time_collection = db["time"]

class room(BaseModel):
    room : int
    status : int
    arrive_time : int

class time(BaseModel):
    duration : int
    total_time: int
    count : int

class status(BaseModel):
    toilet_state1 : int
    toilet_state2 : int
    toilet_state3 : int

def calc_time():
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    second = now.second
    time = hour*3600 + minute * 60 + second
    return time

@app.post("/toilet/update/")
def update_toilet(state:status):
    s = jsonable_encoder(state)
    state1 = s["toilet_state1"]  
    state2 = s["toilet_state2"] 
    state3 = s["toilet_state3"]    
    loca1 = room_collection.find_one({"room" : 1})
    loca2 = room_collection.find_one({"room" : 2})
    loca3 = room_collection.find_one({"room" : 3})
    if state1 != loca1["status"]:
        roomNum = 1
        status = state1
        loca = loca1
    elif state2 != loca2["status"]:
        roomNum = 2
        loca = loca2
        status = state2
    elif state3 != loca3["status"]:
        loca = loca3
        roomNum = 3
        status = state3
    query = { "room": roomNum}   
    present_time = calc_time()
    if status == 1:
        room_collection.update_one(query, { "$set": {"status": status,"arrive_time":present_time, "duration" : 0}})
    else:    
        localtime = time_collection.find_one()
        count = localtime["count"] + 1
        duration = present_time - loca["arrive_time"] 
        total_time = localtime["total_time"] + duration
        update_status = {"$set" :{"status" :status}}
        update_time = {"$set" : {"duration":duration,"total_time":total_time,"count":count}}
        room_collection.update_one(query, update_status)
        time_collection.update_one({"count":count-1}, update_time)
    

@app.get("/")
def returndata():
    res1 = room_collection.find_one({"room":1})
    current_time = calc_time()
    status1 = res1["status"]
    arrive1 = res1["arrive_time"]
    duration1 = current_time-arrive1

    res2 = room_collection.find_one({"room":2})
    current_time = calc_time()
    status2 = res2["status"]
    arrive2 = res2["arrive_time"]
    duration2 = current_time-arrive2

    res3 = room_collection.find_one({"room":3})
    current_time = calc_time()
    status3 = res3["status"]
    arrive3 = res3["arrive_time"]
    duration3 = current_time-arrive3

    time = time_collection.find_one()
    total_time = time["total_time"]
    count = time["count"]

    average_time = total_time/count
    most_dur = max(duration1,duration2,duration3)
    estimate = 0
    if(most_dur < average_time):
        estimate = average_time - most_dur

    return{
            "toilet" : [{
            "id" : 1,
            "status" : status1,
            "arrive" : arrive1,
            "duration" : duration1},
            {
            "id" : 2,
            "status" : status2,
            "arrive" : arrive2,
            "duration" : duration2},
                {
            "id" : 3, 
            "status" : status3,
            "arrive" : arrive3,
            "duration" : duration3}],
            "estimate" : estimate
        }  