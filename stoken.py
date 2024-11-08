from itsdangerous import URLSafeTimedSerializer
from configy import secret_key,salt
def token(data):
    serializer=URLSafeTimedSerializer(secret_key)
    return serializer.dumps(data,salt=salt)
def dtoken(data):
    serailzer=URLSafeTimedSerializer(secret_key)
    return serailzer.loads(data,salt=salt)