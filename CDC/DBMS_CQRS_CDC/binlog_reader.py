from pymysqlreplication import BinLogStreamReader
from pymysqlreplication.row_event import (
    UpdateRowsEvent,
    WriteRowsEvent,
    DeleteRowsEvent
)
from config import settings
from EventHandler import handle_insert_event, handle_update_event, handle_delete_event
import time

def start_binlog_stream():
    while True:
        try:
            stream = BinLogStreamReader(
                connection_settings={
                    'host': settings.mysql_host,
                    'port': settings.mysql_port,
                    'user': settings.mysql_user,
                    'passwd': settings.mysql_password,
                },
                server_id=settings.mysql_server_id,
                blocking=True,
                resume_stream=True,
                only_events=[WriteRowsEvent, UpdateRowsEvent, DeleteRowsEvent],
                only_tables=['a', 'b'],  # 모니터링할 테이블
                only_schemas=['db']
            )

            for binlogevent in stream:
                for row in binlogevent.rows:
                    event = {}
                    if isinstance(binlogevent, WriteRowsEvent):
                        event = row["values"]
                        handle_insert_event(event)
                    elif isinstance(binlogevent, UpdateRowsEvent):
                        event = row["after_values"]
                        handle_update_event(event)
                    elif isinstance(binlogevent, DeleteRowsEvent):
                        event = row["values"]
                        handle_delete_event(event)
                        
        except Exception as e:
            print(f"Binlog Stream Error: {e}")
            time.sleep(5)  # 잠시 대기 후 재시도