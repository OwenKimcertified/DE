from sqlalchemy.orm import sessionmaker

from DBMS import engine, DenormalizedData
from schemas_dto import DenormalizedDataSchema 

Session = sessionmaker(bind = engine)

def handle_insert_event(event):
    session = Session()
    try:
        denormalized_record = DenormalizedDataSchema(**event)
        denormalized_data = DenormalizedData(
                                            user_id=denormalized_record.user_id,
                                            user_name=denormalized_record.user_name,
                                            order_id=denormalized_record.order_id,
                                            order_details=denormalized_record.order_details,
                                            updated_at=denormalized_record.updated_at
                                            )
        session.add(denormalized_data)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Insert Event Handling Error: {e}")
    finally:
        session.close()

def handle_update_event(event):
    session = Session()
    try:
        record = session.query(DenormalizedData).filter_by(order_id=event.get('order_id')).first()
        if record:
            record.order_details = event.get('order_details')
            record.updated_at = event.get('timestamp')
            session.commit()
    except Exception as e:
        session.rollback()
        print(f"Update Event Handling Error: {e}")
    finally:
        session.close()

def handle_delete_event(event):
    session = Session()
    try:
        record = session.query(DenormalizedData).filter_by(order_id=event.get('order_id')).first()
        if record:
            session.delete(record)
            session.commit()
    except Exception as e:
        session.rollback()
        print(f"Delete Event Handling Error: {e}")
    finally:
        session.close()