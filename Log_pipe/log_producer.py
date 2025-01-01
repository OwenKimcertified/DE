import random
import json
from datetime import datetime, timedelta
import time
from confluent_kafka import Producer

# 로그 생성 함수들 (변경 없음)
def generate_user_id():
    return f"user_{random.randint(1000, 9999)}"

def generate_device_and_region():
    devices = ["mobile", "desktop", "tablet"]
    regions = ["Seoul", "Busan", "Incheon", "Daegu", "Daejeon", "Gwangju", "Ulsan"]
    return random.choice(devices), random.choice(regions)

def generate_action():
    actions = ["view_item", "add_to_cart", "remove_from_cart", "checkout", "purchase", "click_banner"]
    return random.choice(actions)

def generate_category():
    categories = ["electronics", "clothing", "beauty", "sports", "books", "furniture"]
    return random.choice(categories)

def generate_order_method():
    methods = ["credit_card", "paypal", "bank_transfer", "mobile_payment"]
    return random.choice(methods)

def generate_order_success():
    return random.choice([True, False])

def generate_revisit_data():
    return random.choice([True, False])

def generate_log():
    user_id = generate_user_id()
    device, region = generate_device_and_region()
    action = generate_action()
    category = generate_category()
    order_method = generate_order_method()
    order_success = generate_order_success()
    revisit = generate_revisit_data()
    banner_click_id = f"banner_{random.randint(1, 50)}" if action == "click_banner" else None
    timestamp = datetime.now() - timedelta(seconds=random.randint(0, 3600))

    log = {
        "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "user_id": user_id,
        "device": device,
        "region": region,
        "action": action,
        "category": category if action in ["view_item", "add_to_cart", "purchase"] else None,
        "order_method": order_method if action == "purchase" else None,
        "order_success": order_success if action == "purchase" else None,
        "revisit": revisit,
        "banner_click_id": banner_click_id,
    }
    return log

# Kafka 프로듀서 설정
def create_kafka_producer():
    conf = {
        'bootstrap.servers': 'localhost:9092',  # Kafka 서버 주소
        'client.id': 'python-producer',
    }
    producer = Producer(conf)
    return producer

# Kafka에 로그 전송
def send_log_to_kafka(producer, log, topic, partition):
    try:
        producer.produce(topic, value=json.dumps(log, ensure_ascii=False).encode('utf-8'), partition=partition)
        producer.flush()  # 데이터를 전송
    except Exception as e:
        print(f"Error producing message: {e}")

# 초당 300개 로그 생성 및 Kafka로 전송
def generate_logs_per_second(num_logs_per_second, duration_seconds, producer, topic):
    num_partitions = 3  # 파티션 수 설정
    for _ in range(duration_seconds):  # duration_seconds 동안 반복
        logs = [generate_log() for _ in range(num_logs_per_second)]
        for i, log in enumerate(logs):
            partition = i % num_partitions  # 파티션을 순차적으로 나누기
            send_log_to_kafka(producer, log, topic, partition)
        time.sleep(1)  # 1초 대기

def generate_log():
    # 예시 로그 생성 함수
    return {"user_id": 123, "action": "login", "timestamp": time.time()}

if __name__ == "__main__":
    topic = "user_log2"  # Kafka topic 이름
    producer = create_kafka_producer()  # Kafka 프로듀서 생성

    num_logs_per_second = 300  # 초당 생성할 로그 수
    duration_seconds = 10  # 실행 시간 (초 단위)
    generate_logs_per_second(num_logs_per_second, duration_seconds, producer, topic)