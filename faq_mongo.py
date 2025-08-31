# faq_mongo.py
import motor.motor_asyncio

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "faqbot"
COLLECTION_NAME = "faq"

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

async def get_all_faq():
    cursor = collection.find({})
    faq = {}
    async for doc in cursor:
        faq[doc["category"]] = doc.get("questions", {})
    return faq

async def get_all_categories():
    cursor = collection.find({}, {"category": 1})
    categories = []
    async for doc in cursor:
        categories.append(doc["category"])
    return categories

async def get_faq_by_category(category):
    doc = await collection.find_one({"category": category})
    if doc:
        return doc.get("questions", {})
    return {}

async def add_category(category):
    existing = await collection.find_one({"category": category})
    if existing:
        return False
    await collection.insert_one({"category": category, "questions": {}})
    return True

async def rename_category(old_name, new_name):
    existing = await collection.find_one({"category": new_name})
    if existing:
        return False
    result = await collection.update_one({"category": old_name}, {"$set": {"category": new_name}})
    return result.modified_count > 0

async def delete_category(category):
    result = await collection.delete_one({"category": category})
    return result.deleted_count > 0

async def add_question(category, question, answer):
    doc = await collection.find_one({"category": category})
    if not doc:
        return False
    questions = doc.get("questions", {})
    if question in questions:
        return False
    questions[question] = answer
    result = await collection.update_one(
        {"category": category},
        {"$set": {"questions": questions}}
    )
    return result.modified_count > 0

async def edit_answer(category, question, new_answer):
    doc = await collection.find_one({"category": category})
    if not doc:
        return False
    questions = doc.get("questions", {})
    if question not in questions:
        return False
    questions[question] = new_answer
    result = await collection.update_one(
        {"category": category},
        {"$set": {"questions": questions}}
    )
    return result.modified_count > 0

async def delete_question(category, question):
    doc = await collection.find_one({"category": category})
    if not doc:
        return False
    questions = doc.get("questions", {})
    if question not in questions:
        return False
    del questions[question]
    result = await collection.update_one(
        {"category": category},
        {"$set": {"questions": questions}}
    )
    return result.modified_count > 0

