from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from bson import ObjectId
import uvicorn
import os

app = FastAPI()

# -------------------- CORS --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- MongoDB --------------------
# ✅ BEST PRACTICE: Use environment variable
MONGO_URL = os.getenv(
    "MONGO_URL",
    "mongodb+srv://Anu21:abcdefghijk@travelappcluster.moid68x.mongodb.net/?appName=TravelAppCluster"
)

client = MongoClient(MONGO_URL)
db = client["travelDB"]

users_collection = db["users"]
bookings_collection = db["bookings"]
wishlist_collection = db["wishlist"]

print("✅ MongoDB Connected")

# -------------------- GLOBAL ERROR HANDLER --------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [err['msg'] for err in exc.errors()]
    return JSONResponse(
        status_code=422,
        content={"message": ", ".join(errors)}
    )

# -------------------- MODELS --------------------
class User(BaseModel):
    name: str
    email: str
    password: str

class LoginData(BaseModel):
    email: str
    password: str

class BookingRequest(BaseModel):
    user_email: str
    airline: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    date: str
    passengers: int
    price: float

class WishlistCreate(BaseModel):
    user_id: str
    place_name: str
    image_url: str
    rating: str

# -------------------- AUTH --------------------
@app.post("/register")
def register(user: User):
    try:
        if users_collection.find_one({"email": user.email}):
            raise HTTPException(status_code=400, detail="Email already exists")

        users_collection.insert_one(user.dict())
        return {"message": "User registered successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/login")
def login(data: LoginData):
    try:
        user = users_collection.find_one({"email": data.email})

        if not user or user["password"] != data.password:
            raise HTTPException(status_code=400, detail="Invalid credentials")

        return {
            "message": "Login successful",
            "user": {
                "name": user["name"],
                "email": user["email"],
                "userId": str(user["_id"])
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- WISHLIST --------------------
@app.post("/wishlist")
def add_to_wishlist(item: WishlistCreate):
    try:
        if not item.user_id:
            raise HTTPException(status_code=400, detail="User not logged in")

        exists = wishlist_collection.find_one({
            "user_id": item.user_id,
            "place_name": item.place_name
        })

        if exists:
            raise HTTPException(status_code=400, detail="Already in wishlist")

        wishlist_collection.insert_one(item.dict())
        return {"message": "Added to wishlist"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/wishlist/{user_id}")
def get_wishlist(user_id: str):
    try:
        items = []

        for item in wishlist_collection.find({"user_id": user_id}):
            item["_id"] = str(item["_id"])
            items.append(item)

        return items

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/wishlist/{item_id}")
def remove_from_wishlist(item_id: str):
    try:
        if not ObjectId.is_valid(item_id):
            raise HTTPException(status_code=400, detail="Invalid ID")

        result = wishlist_collection.delete_one({"_id": ObjectId(item_id)})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Item not found")

        return {"message": "Removed from wishlist"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- BOOKINGS --------------------
@app.post("/book-flight")
def book_flight(booking: BookingRequest):
    try:
        # ✅ Check user exists
        user = users_collection.find_one({"email": booking.user_email})

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        booking_doc = {
            "user_email": booking.user_email,
            "flight_details": {
                "airline": booking.airline,
                "origin": booking.origin,
                "destination": booking.destination,
                "departure_time": booking.departure_time,
                "arrival_time": booking.arrival_time,
                "date": booking.date,
            },
            "passengers": booking.passengers,
            "total_price": booking.price,
            "status": "confirmed"
        }

        bookings_collection.insert_one(booking_doc)

        return {"message": "Flight booked successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/my-bookings/{email}")
def get_user_bookings(email: str):
    try:
        bookings = []

        for b in bookings_collection.find({"user_email": email}):
            b["_id"] = str(b["_id"])
            b["flight_details"] = b.get("flight_details", {})
            bookings.append(b)

        return bookings

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Change the route from @app.delete to @app.put (or keep delete but change logic)
@app.put("/cancel-booking/{id}")
def cancel_booking(id: str):
    try:
        if not ObjectId.is_valid(id):
            raise HTTPException(status_code=400, detail="Invalid ID")

        # Update status to cancelled instead of deleting
        result = bookings_collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"status": "cancelled"}}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Booking not found")

        return {"message": "Booking cancelled successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# -------------------- HEALTH CHECK --------------------
@app.get("/")
def root():
    return {"message": "API is running 🚀"}


# -------------------- RUN --------------------
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)