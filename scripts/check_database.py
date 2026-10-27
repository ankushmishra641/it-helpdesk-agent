"""Run only against a dedicated staging DB via a securely supplied DATABASE_URL."""
import sys
import uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import database as db
def main():
    db.init_db()
    token=db.new_session()
    sid=db.identify(token)
    row=None
    try:
        row=db.create_ticket(sid,dict(summary='Staging verification request',description='Synthetic database smoke test.',category='General',priority='Low'),str(uuid.uuid4()))
        db.engine.dispose()
        assert db.get_ticket(sid,row['id'])['summary']=='Staging verification request'
        print('Database schema, write, read and connection-reopen checks passed.')
    finally:
        db.clear_session(sid)
        if row:
            assert db.get_ticket(sid,row['id']) is None
        print('Temporary verification session removed.')
if __name__=='__main__':
    main()
